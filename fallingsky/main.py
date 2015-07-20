"""Launcher scripts."""


import pygame

from fallingsky.menu import MainMenu
from fallingsky.game import GameBoard
from fallingsky.util import Coord


# 3:2, 960x640 -- shared resolution between android and ios
STANDARD_RESOLUTION = Coord(960, 640)


def play():
    """Main access point, plays game through the main menu."""

    pygame.init()
    menu = MainMenu(STANDARD_RESOLUTION)
    try:
        menu.run_forever()
    except KeyboardInterrupt:
        raise SystemExit("Interrupted")


def play_hack():
    """Quick and dirty dev/testing/cheating access, skips the main menu."""

    class HackMenu(object):
        data = {             # feel free to edit to your liking
            "user_id": "hacker",
            "wins": 0,
            "losses": 0,
            "width": 10,     # number of blocksize units of gameboard width
            "height": 25,    # number of blocksize units of gameboard height
            "total_score": 0,
            "best_score": 0,
            "nexts": 4,      # how many next blocks you get
            "blocksize": 4,  # this is multiplied by 4 to ensure proper centres
            "fallrate": 1,   # drop speed, aka level. from 1-21
            "bonus_block_rate": 0,  # number of bonus blocks/number of wins
            "spawn_rate": False,  # shows your % shape spawns
        }

        def __init__(self, res):
            self.resolution = res
            self.losses = 0
            self.wins = 0

    # uncomment the next two lines if you want every shape to be a line
    # from fallingsky import shapes
    # shapes.IMADEVELOPER = True

    GameBoard().main(
        pygame.display.set_mode(STANDARD_RESOLUTION),
        HackMenu(STANDARD_RESOLUTION),
    )


if __name__ == "__main__":
    # to hack, run this file directly instead of the fallingsky command
    pygame.init()
    play_hack()
