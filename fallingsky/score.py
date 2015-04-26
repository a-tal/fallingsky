"""Score keeping class and helpers.

Usage:

>>> k = Keeper()
>>> k.game += 1000
>>> k.game_over()
>>> k.total
1000
>>> k.game
0
>>>

"""


class GameScore(object):
    def __init__(self, score=None, last_added=None):
        self._score = score or 0
        self._last_added = last_added or 0
        self._multiplier = 0
        super(GameScore, self).__init__()

    def __add__(self, other):
        return GameScore(self.get_score(), last_added=other)

    def get_score(self):
        """Calculates the current scores after applying multipliers."""

        return self._score + (self._last_added * (self._multiplier or 1))

    def multiply_last(self, multiplier):
        """Adds the multiplier to the last added score."""

        self._multiplier += multiplier

    def __int__(self):
        """Override to call this as int(GameScore)."""

        return self.get_score()

    def __str__(self):
        return str(self.get_score())

    def __repr__(self):
        return "<{}.{} object at {} with value {}>".format(
            __name__, self.__class__.__name__, hex(id(self)), self.get_score()
        )


class TotalScore(int):
    def __add__(self, other):
        return TotalScore(int(self) + int(other))


class Keeper(object):
    def __init__(self):
        self.game = GameScore(0)
        self.total = TotalScore(0)
        self.best = GameScore(0)

    def game_over(self):
        self.total += self.game
        self.best = max(self.best, self.game)
        self.game = GameScore(0)

    def resume(self, previous_total, previous_best):
        self.total = TotalScore(previous_total)
        self.best = GameScore(previous_best)


if __name__ == "__main__":
    k = Keeper()
    k.game += 1000
    print(k.game)
    k.game.multiply_last(2)
    print(k.game.get_score())
    print(repr(k.game))
