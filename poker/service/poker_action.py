from poker.model.poker_model import Game


class PokerAction:
    game: Game

    def __init__(self, game: Game):
        self.game = game

    def act(self, **kwargs):
        pass

    def update_active_player(self, **kwargs):
        pass

    def update_game_state(self, **kwargs):
        pass

    def execute(self, **kwargs):
        self.act(**kwargs)
        self.update_active_player()
        self.update_game_state()
