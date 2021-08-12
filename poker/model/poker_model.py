class Game:
    game_id: str
    game_type: str
    num_seats: int
    big_blind: int
    small_blind: int
    min_buyin: int
    max_buyin: int
    table_name: str
    state_cd: str

    def __init__(self, player_dict: dict):
        for key, value in player_dict.items():
            setattr(self, key, value)


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

    def __init__(self, player_dict: dict):
        for key, value in player_dict.items():
            setattr(self, key, value)
