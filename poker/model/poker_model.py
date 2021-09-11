from poker.repo.poker_repo import *
from typing import List
from enum import Enum
import random


class Player:
    game_id: str
    user_id: str
    seat_num: int
    buyin: int
    stack: int
    is_active: bool
    sitting_out: bool
    position: int
    bet_amt: int
    amt_in_pot: int
    has_folded: bool
    has_acted: bool
    hand: str

    def __init__(self, player_dict: dict):
        for key, value in player_dict.items():
            setattr(self, key, value)

    def reset(self):
        self.is_active = False
        self.amt_in_pot = 0
        self.bet_amt = 0
        self.has_folded = False
        self.has_acted = False
        self.hand = ''

    def bet(self, bet_amt):
        if bet_amt > self.stack:
            raise Exception(f'Invalid bet amt. Bet amt ({bet_amt}) is greater than player\'s stack ({self.stack})')
        self.bet_amt += bet_amt
        self.stack -= bet_amt

    def fold(self):
        self.has_folded = True


class Players:
    players: List[Player]

    def __init__(self, players_dict: List[dict]):
        self.players = [Player(p) for p in players_dict]
        self.players.sort(key=lambda x: x.seat_num)

    def get_sitting_players(self) -> List[Player]:
        return [p for p in self.players if not p.sitting_out]

    def init_positions(self):
        for i, p in enumerate(self.get_sitting_players()):
            p.position = i+1

    def set_initial_active(self):
        players = self.get_sitting_players()
        bets = {p.bet_amt for p in players}
        if len(bets) == 1 and bets.pop() == 0:
            players[0].is_active = True
        elif len(players) > 2:
            players[2].is_active = True
        else:
            players[0].is_active = True

    def get_small_blind(self):
        return self.get_sitting_players()[0]

    def get_big_blind(self):
        return self.get_sitting_players()[1]

    def get_player(self, user_id) -> Player:
        return next(p for p in self.players if p.user_id==user_id)

    def highest_bet(self) -> int:
        return max(p.bet_amt for p in self.players)

    def all_have_acted(self):
        return all(p.has_acted for p in self.players
                   if not p.sitting_out and not p.has_folded)

    def bets_are_equal(self):
        bets = {p.bet_amt for p in self.players
                if not p.sitting_out and not p.has_folded}
        return len(bets)==1


class State(Enum):
    STARTING = 1
    PREFLOP = 2
    FLOP = 3
    TURN = 4
    RIVER = 5


new_deck = 'Ad2d3d4d5d6d7d8d9dTdJdQdKd' + \
           'Ac2c3c4c5c6c7c8c9cTcJcQcKc' + \
           'Ah2h3h4h5h6h7h8h9hThJhQhKh' + \
           'As2s3s4s5s6s7s8s9sTsJsQsKs'


class Game:
    game_id: str
    game_type: str
    num_seats: int
    big_blind: int
    small_blind: int
    min_buyin: int
    max_buyin: int
    table_name: str
    state_cd: State
    players: Players
    pot_amt: int
    board: str
    deck: str

    def __init__(self, game_dict: dict, players_dict: List[dict]):
        for key, value in game_dict.items():
            if key == 'state_cd':
                setattr(self, key, State[value])
            else:
                setattr(self, key, value)
        self.deck = new_deck
        self.board = ''
        self.players = Players(players_dict)

    def post_blinds(self):
        sitting_players = self.players.get_sitting_players()
        sb = sitting_players[0]
        bb = sitting_players[1]
        sb.bet(self.small_blind)
        bb.bet(self.big_blind)

    def shuffle_deck(self):
        cards = [self.deck[i:i+2] for i in range(0, len(self.deck), 2)]
        random.shuffle(cards)
        self.deck = ''.join(cards)

    def collect_bets(self):
        for p in self.players.get_sitting_players():
            p.amt_in_pot += p.bet_amt
            self.pot_amt += p.bet_amt
            p.bet_amt = 0

    def deal_flop(self):
        self.board = self.deck[:6]
        self.deck = self.deck[6:]

    def deal_turn_river(self):
        self.board += self.deck[:2]
        self.deck = self.deck[2:]

    def deal_hands(self):
        for p in self.players.get_sitting_players():
            p.hand = self.deck[:2]
            self.deck = self.deck[2:]

    def init_round(self, state_cd):
        self.state_cd = state_cd
        if state_cd in (State.FLOP, State.TURN, State.RIVER):
            self.collect_bets()
        if state_cd == State.PREFLOP:
            print('setting positions')
            self.players.init_positions()
            print('posting blinds')
            self.post_blinds()
            print('dealing hands')
            self.deal_hands()
        elif state_cd == State.FLOP:
            self.deal_flop()
        elif state_cd == State.TURN:
            self.deal_turn_river()
        elif state_cd == State.RIVER:
            self.deal_turn_river()
        self.players.set_initial_active()


    def is_end_of_round(self):
        return (self.state_cd in (State.PREFLOP, State.FLOP, State.TURN, State.RIVER)
                and self.players.all_have_acted()
                and self.players.bets_are_equal())

    def update_state(self, db):
        print('updating state')
        sitting_players = self.players.get_sitting_players()
        changed = False
        if self.state_cd == State.STARTING and len(sitting_players) > 1:
            print('starting preflop')
            self.init_round(State.PREFLOP)
            changed = True
        elif self.is_end_of_round():
            if self.state_cd != State.RIVER:
                next_state = State(self.state_cd.value + 1)
                self.init_round(next_state)
            else:
                pass
            changed = True
        if changed:
            self.update_db(db)

    def update_db(self, db):
        update_players(db, [vars(p) for p in self.players.players])
        game_dict = vars(self)
        del game_dict['players']
        game_dict['state_cd'] = self.state_cd.name
        update_game(db, game_dict)

    def act(self, db, action_cd, user_id, **kwargs):
        player = self.players.get_player(user_id)
        if action_cd == 'check_call':
            highest_bet = self.players.highest_bet()
            if player.bet_amt < highest_bet:
                player.bet(highest_bet)
        if action_cd == 'check_fold':
            if player.bet_amt < self.players.highest_bet():
                player.fold()
        if action_cd == 'bet':
            bet_amt = kwargs['bet_amt']
            player.bet(bet_amt)
        player.has_acted = True
        self.update_state(db)
