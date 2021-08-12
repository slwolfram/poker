from poker.model.poker_model import *


def get_players_table(db):
    return db.get_table('players')


def get_games_table(db):
    return db.get_table('games')


def get_games(db):
    return list(get_games_table(db))


def get_game(db, game_id):
    return Game(get_games_table(db).find_one(game_id=game_id))


def update_game(db, game: dict):
    games = db['games']
    games.update(game, ['game_id'])


def insert_game(db, game: dict):
    game['state_cd'] = 'STARTING'
    db['games'].insert(game)


def add_player(db, player: dict):
    db['players'].insert(player)


def get_players(db, game_id):
    players = get_players_table(db)
    return [Player(p) for p in
            list(players.find(game_id=game_id))]


def update_players(db, players):
    if type(players[0]) == Player:
        players = [vars(p) for p in players]
    players_db = db['players']
    for p in players:
        players_db.update(p, ['game_id', 'user_id'])

