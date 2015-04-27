# coding: utf-8
"""Holds the MainMenu object and between-game interaction."""


from __future__ import unicode_literals

import os
import pygame
from kezmenu import KezMenu

from fallingsky.game import GameBoard
from fallingsky.user import get_users
from fallingsky.user import UserData
from fallingsky.user import reset_users
# from fallingsky.util import load_image


class MainMenu(object):
    """The Main menu object class which contains all children.

    Initialized with the screen resolution as an (x, y) tuple
    """

    def __init__(self, resolution, *args, **kwargs):
        self.resolution = resolution
        self.default_name = "Player 1"
        self.running = True
        self.updating_name = False
        self.help = False
        self.buffer = 5  # px
        self.font = pygame.font.SysFont("arial", 20)
        super(MainMenu, self).__init__(*args, **kwargs)

    def load_player_data(self, player_name=None):
        """Loads the player's data, or default_name's."""

        self.player_name = player_name or self.default_name
        self.data = UserData(self.player_name)

    def run_forever(self):
        """Maybe not quite forever, but until the user quits."""

        # start the screen object
        screen = pygame.display.set_mode(self.resolution)
        clock = pygame.time.Clock()
        # background = load_image("background.png")

        users = get_users()
        if len(users) == 1:
            self.load_player_data(os.path.splitext(users[0])[0])
        else:
            self.load_player_data()  # TODO: player listing

        self.menu = KezMenu(
            ["Arcade Mode", lambda: GameBoard().main(screen, self)],
            [self.player_name, self.update_player_name],
            ["Controls", lambda : setattr(self, "help", not self.help)],
            ["Reset Scores", self.reset_scores],
            ["Quit", lambda: setattr(self, 'running', False)],
        )
        # TODO: change this. should make a player screen where they can see
        #       what accounts have been made locally, what their stats are,
        #       what their upper limits are, rename them, cheat, etc...
        PLAYER_INDEX = 1  # index of the player's name

        self.menu.x = self.resolution[0] // 3
        self.menu.y = self.resolution[1] // 2
        # self.menu.enableEffect('raise-col-padding-on-focus', enlarge_time=0.1)

        render = lambda x : self.font.render(x, True, (222, 222, 222))

        while self.running:
            events = pygame.event.get()

            if self.updating_name is True:
                events = self.handle_namechange(events)

            if self.player_name == self.default_name:
                menu_name = "{} -- Click to change".format(self.default_name)
            else:
                menu_name = self.player_name
            self.menu.options[PLAYER_INDEX]["label"] = menu_name

            self.menu.update(events, clock.tick(30) / 1000.0)
            screen.fill((99, 99, 99))  # TODO: make better
            # screen.blit(background, (0, 0))

            if self.help:
                # add controls/help to bottom
                controls = [
                    # "-- Controls --",
                    "left: ← or A",
                    "right: → or D",
                    "down: ↓ or S",
                    "rotate clockwise: ↑, W, or E",
                    "rotate counter-clockwise: Q",
                    "hold/swap: H",
                    "slam down: space bar",
                    "pause: P",
                ]

                # get the largest possible control label size
                control_size = self.font.size(max(controls, key=len))

                  # px buffer
                for i, control in enumerate(controls):
                    screen.blit(render(control), (
                        self.resolution[0] - (control_size[0] + self.buffer),
                        self.resolution[1] - (
                            (control_size[1] * len(controls)) -
                            (i * control_size[1]) + self.buffer
                        )
                    ))

            if self.data["wins"] or self.data["losses"]:
                label = "wins: {wins} losses: {losses}".format(**self.data.data)
                win_loss = render(label)
                win_loss_size = self.font.size(label)
                screen.blit(win_loss, (
                    (self.resolution[0] / 2) - (win_loss_size[0] / 2),
                    self.buffer,
                ))

            self.menu.draw(screen)
            pygame.display.flip()

    def handle_namechange(self, events):
        """Proccess events during a name change."""

        scrubbed_events = []
        for event in events:
            if "KeyDown" in pygame.event.event_name(event.type):
                if event.key == 27:  # esc/cancel
                    self.player_name = self._old_player_name
                    self.update_player_name()
                elif event.key in (92, 8):  # backspace(s)
                    self.player_name = self.player_name[:-1]
                elif event.key not in (13,):  # 13 == enter
                    try:
                        key = chr(event.key)
                    except ValueError:
                        if event.key not in range(273, 277):
                            scrubbed_events.append(event)
                    else:
                        if pygame.key.get_mods() in (1, 8192):
                            # checks for shift or caps lock, and both
                            key = key.capitalize()
                        self.player_name += key
                else:
                    scrubbed_events.append(event)
            else:
                scrubbed_events.append(event)

        # 2nd item in the list is the players name, update it
        return scrubbed_events

    def update_player_name(self):
        """Called when someone clicks on the player name."""

        if self.updating_name:
            # the 'or' here is to catch hitting enter twice with no new input
            self.load_player_data(self.player_name or self._old_player_name)
            self.menu.mouse_enabled = True
            self._old_player_name = None
            self.updating_name = False
        else:
            self.updating_name = True
            self._old_player_name = self.player_name  # save this for cancel
            self.player_name = ""
            self.menu.mouse_enabled = False

    def reset_scores(self):
        """Called to reset all user data and reload this player's data."""

        reset_users()
        self.load_player_data(self.player_name)
