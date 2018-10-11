import time
import json
import uuid
import copy
import logging
import football
from gevent import monkey
from ws4py.websocket import WebSocket
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication


monkey.patch_all()
games = {}


class ErrorToClient(Exception):
    pass


class GameConnections:

    def __init__(self, id):
        self.id = id
        self.teams = []
        self.viewers = []
        self.state = 'waiting-for-teams'
        self.token = None
        self.game = football.Game()
        self.turn = 1

    def add_connection(self, action, connection):
        if action not in ('play', 'view'):
            raise ErrorToClient('invalid action', action)
        if action == 'view':
            self.viewers.append(connection)
            return
        if self.state != 'waiting-for-teams':
            raise ErrorToClient('both teams are already here')
        self.teams.append(connection)
        self.send_to_all(message='team joined', team_no=len(self.teams))
        if len(self.teams) == 2:
            self.state = 'both-teams-ready'
            self.start_game()

    def start_game(self):
        self.send_to_all(field=self.game.field.get_data())
        self.send_state()
        self.next_frame_token()
        self.game.start_time = time.time()

    def remove_connection(self, conn):
        if conn in self.viewers:
            self.viewers.remove(conn)
        elif conn in self.teams:
            self.teams.remove(conn)
            self.state = 'team-disconnected'

    def next_frame_token(self):
        self.turn = int(not self.turn)
        self.token = int(uuid.uuid4().hex[0], 16)
        team = self.teams[self.turn]
        self.send_to_team(team, token=self.token)

    def send_to_all(self, **kw):
        msg = json.dumps(kw)
        for conn in self.teams + self.viewers:
            conn.send(msg)

    def send_to_team(self, team_conn, **kw):
        msg = json.dumps(kw)
        team_conn.send(msg)

    def send_to_viewers(self, **kw):
        msg = json.dumps(kw)
        for conn in self.viewers:
            conn.send(msg)

    def received_message(self, msg, team):
        token = msg[0]
        if token != self.token:
            raise ErrorToClient('invalid token')
        if team != self.teams[self.turn]:
            raise ErrorToClient('invalid turn')
        self.process_message(msg)

    def process_message(self, msg):
        self.game.process_message(self.turn, msg[1:])
        self.send_state()
        if self.game.goal:
            team = self.game.get_attacking_team()
            self.send_to_all(goal=True, team=team)
            self.game.sleep(2)
            self.game.set_init_position(give_ball_to=int(not team))
            self.game.goal = False
            self.send_state()
            self.game.sleep(1)
        self.next_frame_token()

    def customized_state(self, data, team_no):
        d = copy.copy(data)
        d['ours'] = d.pop('team%d' % team_no)
        d['theirs'] = d.pop('team%d' % (not team_no))
        return d

    def send_state(self):
        data = self.game.get_data()
        rtl_data = self.game.get_data(rtl=True)
        team_0_data = self.customized_state(data, 0)
        team_1_data = self.customized_state(rtl_data, 1)
        self.send_to_team(self.teams[0], state=team_0_data)
        self.send_to_team(self.teams[1], state=team_1_data)
        self.send_to_viewers(state=data)


class Connection(WebSocket):

    def opened(self):
        self.game = None
        self.safe_call(self.init)

    def safe_call(self, method, *args):
        try:
            method(*args)
        except ErrorToClient as err:
            self.send(json.dumps({'error': True, 'message': err.args[0], 'args': err.args[1:]}))

    def init(self):
        self.set_game()

    def set_game(self):
        route = self.environ['PATH_INFO']
        vals = route[1:].split('/')
        if len(vals) != 2:
            raise ErrorToClient('invalid route', route)
        action, game_id = vals
        if game_id not in games:
            games[game_id] = GameConnections(game_id)
        game = games[game_id]
        game.add_connection(action, self)
        self.game = game

    def closed(self, code, reason=None):
        if self.game:
            self.game.remove_connection(self)

    def received_message(self, message):
        if self.game is None:
            return
        data = message.data.decode()
        self.safe_call(self.on_message, data)

    def on_message(self, data):
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            raise ErrorToClient('invalid json data')
        if type(msg) != list or len(msg) != 5:
            raise ErrorToClient('invalid data')
        self.game.received_message(msg, self)


server = WSGIServer(('localhost', 9000), WebSocketWSGIApplication(handler_cls=Connection))
server.serve_forever()
