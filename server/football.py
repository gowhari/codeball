import time
import math
import config
import logging


def points_distance(x1, y1, x2, y2):
    return abs((x1 + y1 * 1j) - (x2 + y2 * 1j))


class Field:

    def __init__(self):
        self.width = config.field.width
        self.height = config.field.height
        self.goal_size = config.field.goal_size
        self.goal_start = self.height / 2 - config.field.goal_size / 2
        self.goal_end = self.height / 2 + config.field.goal_size / 2

    def get_data(self):
        return {'width': self.width, 'height': self.height, 'goal_size': self.goal_size}


class Ball:

    def __init__(self, game):
        self.game = game
        self.x = 0
        self.y = 0
        self.direction = 0
        self.speed = 0
        self.set_init_position()

    def set_init_position(self, give_ball_to=None):
        self.x = config.field.width / 2
        self.y = config.field.height / 2
        self.direction = 0
        self.speed = 0
        if give_ball_to is not None:
            self.direction = 0 if give_ball_to == 1 else 180
            self.speed = 10

    def move(self):
        self.x += self.speed * math.cos(self.direction * math.pi / 180) * 0.01
        self.y -= self.speed * math.sin(self.direction * math.pi / 180) * 0.01
        field = self.game.field
        if (self.x < 0 or self.x > field.width) and (field.goal_start < self.y < field.goal_end):
            return True
        self.speed -= 0.1
        if self.speed < 0:
            self.speed = 0
        field = self.game.field
        if self.y < 0:
            self.y = 0
            self.direction = -self.direction % 360
        if self.y > field.height:
            self.y = field.height
            self.direction = -self.direction % 360
        if self.x < 0:
            self.x = 0
            self.direction = (180 - self.direction) % 360
        if self.x > field.width:
            self.x = field.width
            self.direction = (180 - self.direction) % 360
        return False

    def get_data(self, rtl=False):
        width = self.game.field.width
        return {
            'x': width - self.x if rtl else self.x,
            'y': self.y,
            'direction': (180 - self.direction) % 360 if rtl else self.direction,
            'speed': self.speed,
        }


class Player:

    def __init__(self, team, num):
        self.team = team
        self.num = num
        self.x = 0
        self.y = 0
        self.set_init_position()

    def set_init_position(self):
        self.x = 1 if self.team.num == 0 else config.field.width - 1
        self.y = config.field.height / 2 + self.num - 1

    def get_data(self, rtl=False):
        width = self.team.game.field.width
        return {'x': width - self.x if rtl else self.x, 'y': self.y}


class Team:

    def __init__(self, game, num):
        self.game = game
        self.num = num
        self.players = [Player(self, i) for i in range(config.game.num_of_players)]

    def set_init_position(self):
        for i in self.players:
            i.set_init_position()

    def update_players(self, data):
        for i, p in enumerate(self.players):
            d = data[i]
            if self.num == 1:
                d['x'] = self.game.field.width - d['x']
            if not self.is_valid_move(p, d):
                continue
            p.x = d['x']
            p.y = d['y']

    def is_valid_move(self, p, d):
        dist = points_distance(p.x, p.y, d['x'], d['y'])
        return dist <= config.game.max_player_move

    def get_data(self, rtl=False):
        return [i.get_data(rtl) for i in self.players]


class Game:

    def __init__(self):
        self.field = Field()
        self.ball = Ball(self)
        self.teams = [Team(self, 0), Team(self, 1)]
        self.goal = False
        self.start_time = None
        self.stoppage_time = 0
        self.score = [0, 0]

    def process_message(self, turn, msg):
        team = self.teams[turn]
        team.update_players(msg['players'])
        self.process_kick(msg['kick'], team)
        self.process_ball()

    def process_kick(self, kick, team):
        if kick is None:
            return
        if kick['speed'] > config.game.max_kick_speed:
            return
        player = team.players[kick['player']]
        if points_distance(player.x, player.y, self.ball.x, self.ball.y) > config.game.max_distance_to_kick:
            return
        self.ball.speed = kick['speed']
        direction = kick['direction']
        if team.num == 1:
            direction = (180 - direction) % 360
        self.ball.direction = direction

    def process_ball(self):
        self.goal = self.ball.move()
        if self.goal:
            self.score[self.get_attacking_team()] += 1

    def get_attacking_team(self):
        assert self.goal is True
        return 1 if self.ball.x < 0 else 0

    def set_init_position(self, give_ball_to=None):
        for i in self.teams:
            i.set_init_position()
        self.ball.set_init_position(give_ball_to)

    def get_data(self, rtl=False):
        return {
            'team0': self.teams[0].get_data(rtl),
            'team1': self.teams[1].get_data(rtl),
            'ball': self.ball.get_data(rtl),
            'time': self.get_time(),
            'score': self.score,
        }

    def get_time(self):
        return 0 if self.start_time is None else time.time() - self.start_time - self.stoppage_time

    def sleep(self, sec):
        time.sleep(sec)
        self.stoppage_time += sec
