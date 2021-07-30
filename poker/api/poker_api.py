from flask_restx import Namespace, Resource
import uuid
import datetime
from poker.db import get_db
from poker.api.util import token_required


api = Namespace('poker')


game_parser = api.parser()
game_parser.add_argument('game_type',   type=str, required=True, location='json')
game_parser.add_argument('num_seats',   type=int, required=True, location='json')
game_parser.add_argument('big_blind',   type=int, required=True, location='json')
game_parser.add_argument('small_blind', type=int, required=True, location='json')
game_parser.add_argument('min_buyin',   type=int, required=True, location='json')
game_parser.add_argument('max_buyin',   type=int, required=True, location='json')
game_parser.add_argument('table_name',  type=str, required=True, location='json')


player_parser = api.parser()
player_parser.add_argument('user_id',  type=int, required=True, location='json')
player_parser.add_argument('game_id',  type=int, required=True, location='json')
player_parser.add_argument('seat_num', type=int, required=True, location='json')
player_parser.add_argument('buyin',    type=int, required=True, location='json')


GAME_TYPES = ['texas_holdem']


def get_game(game_ident):
    games = get_db()['games']
    game = games.find_one(ident=game_ident)
    return game


def update_game(game):
    games = get_db()['games']
    games.update(game, ['ident'])


def insert_game(game):
    get_db()['games'].insert(game)


def add_player(game, player):
    get_db()['players'].insert(olayer)


@api.route('/')
class GameList(Resource):
    @api.expect(game_parser)
    @token_required
    def post(self):
        game = game_parser.parse_args()
        if game['game_type'] not in GAME_TYPES:
            return {'message': 'Invalid game type "{}".'.format(game['game_type'])}, 400
        if game['num_seats'] < 2:
            return {'message': 'num_seats must be greater than 2.'}, 400
        if game['big_blind'] <= 0:
            return {'message': 'big_blind must be greater than 0.'}, 400
        if game['small_blind'] <= 0:
            return {'message': 'small_blind must be greater than 0.'}, 400
        if game['small_blind'] >= game['big_blind']:
            return {'message': 'big blind must be greater than small blind.'}, 400
        if game['min_buyin'] <= 0:
            return {'message': 'min_buyin must be greater than 0'}, 400
        if game['max_buyin'] < game['min_buyin']:
            return {'message': 'max_buyin can not be less than min_buyin'}, 400
        game['ident'] = str(uuid.uuid4())
        insert_game(game)
        return game, 201


@api.route('/player/')
class PlayerList(Resource):
    @api.expect(player_parser)
    @token_required
    def post(self):
        player = player_parser.parse_args()
        game = get_game(player['game_id'])
        if player['buyin'] < game['min_buyin']:
            return {'message': 'buyin is less than minimum buyin.'}, 400
        if player['buyin'] > game['max_buyin']:
            return {'message': 'buyin is greater than maximum buyin.'}, 400
        
