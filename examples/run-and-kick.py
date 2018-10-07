import math
import json
import random
from ws4py.client.threadedclient import WebSocketClient


ws_url = 'ws://localhost:9000/play/NEW1'


class Connection(WebSocketClient):

    def opened(self):
        self.state = None
        self.token = None
        self.field = None
        self.kick_in_prev = False

    def received_message(self, message):
        data = json.loads(message.data.decode())
        if 'state' in data:
            self.state = data['state']
        elif 'token' in data:
            self.token = data['token']
            self.action()
        elif 'field' in data:
            self.field = data['field']
        elif 'message' in data:
            pass
        elif 'goal' in data:
            pass
        else:
            assert 0, 'unknown message: %s' % data

    def find_nearest_player(self):
        players = self.state['ours']
        ball = self.state['ball']
        min_dist = self.field['width'] + 1
        player = None
        for p in players:
            d = math.sqrt((ball['x'] - p['x']) ** 2 + (ball['y'] - p['y']) ** 2)
            if d < min_dist:
                player = p
                min_dist = d
        return player

    def move_player_to_ball(self, player):
        ball = self.state['ball']
        dist_x = ball['x'] - player['x']
        dist_y = ball['y'] - player['y']
        dir_x = 1 if dist_x > 0 else -1
        dir_y = 1 if dist_y > 0 else -1
        dist_x = abs(dist_x)
        dist_y = abs(dist_y)
        able_to_kick = dist_x < 0.5 and dist_y < 0.5
        dist_x = min(dist_x, 0.2)
        dist_y = min(dist_y, 0.2)
        player['x'] += dist_x * dir_x
        player['y'] += dist_y * dir_y
        return able_to_kick

    def kick(self):
        if self.kick_in_prev:
            self.kick_in_prev = False
            return None
        self.kick_in_prev = True
        kick_dir = random.randint(-45, 45)
        kick_speed = random.randint(10, 30)
        kick = {'direction': kick_dir, 'speed': kick_speed}
        return kick

    def action(self):
        player = self.find_nearest_player()
        able_to_kick = self.move_player_to_ball(player)
        kick = self.kick() if able_to_kick else None
        players = self.state['ours']
        d = [self.token]
        for p in players:
            d.append([p['x'], p['y']])
        d.append(kick)
        self.send(json.dumps(d))


def main():
    try:
        ws = Connection(ws_url)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()


if __name__ == '__main__':
    main()
