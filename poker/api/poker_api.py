from typing import List
from flask_restx import Namespace, Resource
import uuid
from poker.db import get_db
from poker.model.poker_model import *
from poker.api.util import token_required
from poker.repo.poker_repo import *

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
player_parser.add_argument('user_id',  type=str, required=True, location='json')
player_parser.add_argument('game_id',  type=str, required=True, location='json')
player_parser.add_argument('seat_num', type=int, required=True, location='json')
player_parser.add_argument('buyin',    type=int, required=True, location='json')


GAME_TYPES = ['texas_holdem']



def assign_positions(players: List[Player]):
    pos = 1
    for p in players:
        if not p.sitting_out:
            p.position = pos
            pos += 1


def post_blinds(game: Game, players: List[Player]):
    for p in players:
        if p.position == 1:
            p.bet_amt = game.small_blind
            p.stack = game.small_blind
            p.is_active = True
        elif p.position == 2:
            p.bet_amt = game.big_blind
            p.stack = game.big_blind
            break


def get_player_index_by_position(players: List[Player], position: int) -> int:
    result = -1
    for i, p in enumerate(players):
        if p.position == position:
            result = i
    if result == -1:
        raise Exception(f'No player has a position of {position}.')
    return result


def set_initial_active(players: List[Player]):
    for p in players:
        p.is_active = False
    index = None
    try:
        index = get_player_index_by_position(players, 3)
    except: pass
    if index:
        players[index].is_active = True
    else:
        players[get_player_index_by_position(players, 1)].is_active = True


def update_state(db, game: Game, players: List[Player]):
    if game.state_cd == 'STARTING' and len([p for p in players if not p.sitting_out]) > 1:
        game.state_cd = 'PREFLOP'
        assign_positions(players)
        post_blinds(game, players)
        set_initial_active(players)
        update_players(db, players)
        update_game(db, vars(game))


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
        game['game_id'] = str(uuid.uuid4())
        insert_game(get_db(), game)
        return game, 201


@api.route('/player/')
class PlayerList(Resource):
    @api.expect(player_parser)
    @token_required
    def post(self):
        player = player_parser.parse_args()
        game = get_game(get_db(), player['game_id'])
        if player['buyin'] < game.min_buyin:
            return {'message': 'buyin is less than minimum buyin.'}, 400
        if player['buyin'] > game.max_buyin:
            return {'message': 'buyin is greater than maximum buyin.'}, 400
        player['stack'] = player['buyin']
        player['sitting_out'] = False
        db = get_db()
        add_player(db, player)
        update_state(db, game, get_players(db, game.game_id))
        return player, 200
