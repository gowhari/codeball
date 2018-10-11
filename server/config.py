import logging


logging.basicConfig(level=logging.DEBUG)


game = lambda: None
game.num_of_players = 3
game.max_player_move = 0.3
game.max_kick_speed = 30

field = lambda: None
field.height = 15
field.width = 25
field.goal_size = 3
