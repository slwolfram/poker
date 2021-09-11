from typing import List
from flask_restx import Namespace, Resource as BaseResource
import uuid
from poker.db import get_db
from poker.model.poker_model import *
from poker.api.util import token_required
from poker.repo.poker_repo import *
from injector import inject
from flask_injector import FlaskInjector
import sqlite3

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
player_parser.add_argument('seat_num', type=int, required=True, location='json')
player_parser.add_argument('buyin',    type=int, required=True, location='json')


GAME_TYPES = ['texas_holdem']


class Resource(BaseResource):
    @inject
    def __init__(self, db: sqlite3.Connection, **kwargs):
        self.db = db
        super().__init__(**kwargs)


@api.route('/')
class GameList(Resource):
    @api.expect(game_parser)
    @token_required
    def post(self, user_id):
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
        game['game_id'] = str(uuid.uuid4())
        insert_game(self.db, game)
        return game, 201


@api.route('/<string:game_id>/player/')
class PlayerList(Resource):
    @api.expect(player_parser)
    @token_required
    def post(self, game_id, user_id):
        print(game_id)
        game = get_game(self.db, game_id)
        player = player_parser.parse_args()
        if player['seat_num'] > game['num_seats']:
            return {'message': 'Invalid seat num. Cannot be greater than the maximum seats at the table ({})'.format(game['num_seats'])}, 400
        if player['seat_num'] < 1:
            return {'message': 'Invalid seat num. Cannot be less than 1'}, 400
        for p in get_players(self.db, game_id):
            if p['seat_num'] == player['seat_num']:
                return {'message': 'Seat {} is taken.'.format(player['seat_num'])}, 400
        if player['buyin'] < game['min_buyin']:
            return {'message': 'buyin is less than minimum buyin.'}, 400
        if player['buyin'] > game['max_buyin']:
            return {'message': 'buyin is greater than maximum buyin.'}, 400
        player['user_id'] = user_id
        player['game_id'] = game_id
        player['stack'] = player['buyin']
        player['bet_amt'] = 0
        player['sitting_out'] = False
        player['is_active'] = False
        player['has_acted'] = None
        player['hand'] = ''
        add_player(self.db, player)
        game = Game(game, get_players(self.db, game_id))
        game.update_state(self.db)
        return player, 200


@api.route('/<string:game_id>/player/check_call')
class CheckCall(Resource):
    @token_required
    def get(self, game_id, user_id):
        game = Game(get_game(self.db, game_id), get_players(self.db, game_id))
        game.act(self.db, 'check_call', user_id)
        return '', 200


@api.route('/<string:game_id>/player/check_fold')
class CheckFold(Resource):
    @token_required
    def get(self, game_id, user_id):
        game = Game(get_game(self.db, game_id), get_players(self.db, game_id))
        game.act(self.db, 'check_fold', user_id)
        return '', 200


@api.route('/<string:game_id>/player/bet/<int:bet_amt>')
class Bet(Resource):
    @token_required
    def get(self, game_id, user_id, bet_amt):
        game = Game(get_game(self.db, game_id), get_players(self.db, game_id))
        game.act(self.db, 'bet', user_id, bet_amt=bet_amt)
        return '', 200
