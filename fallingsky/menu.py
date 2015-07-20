# coding: utf-8
"""Holds the MainMenu object and between-game interaction."""


from __future__ import unicode_literals

import os
import pygame
from kezmenu3 import KezMenu

from fallingsky import __version__
from fallingsky.block import Blocks
from fallingsky.game import GameBoard
from fallingsky.user import get_users
from fallingsky.user import UserData
from fallingsky.user import reset_users
from fallingsky.util import load_image


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
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.small_title = pygame.font.SysFont("arial", 24, bold=True)
        self.big_title = pygame.font.SysFont("arial", 108)
        self.magic_sequence = [273, 273, 274, 274, 276, 275, 276, 275, 98, 97]
        self.magic_available = ["width", "height", "nexts", "blocksize",
                                "fallrate", "bonus_block_rate",
                                "spawn_rate"]
        self.magic_enabled = []
        self.magic = []
        self.magical = False
        super(MainMenu, self).__init__(*args, **kwargs)

    def load_player_data(self, player_name=None):
        """Loads the player's data, or default_name's."""

        self.player_name = player_name or self.default_name
        self.data = UserData(self.player_name)

    def run_forever(self):
        """Maybe not quite forever, but until the user quits."""

        # start the screen object
        screen = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption("The Tragedy of the Falling Sky v{}".format(
            __version__
        ))
        clock = pygame.time.Clock()

        users = get_users()
        if len(users) == 1:
            self.load_player_data(os.path.splitext(users[0])[0])
        else:
            self.load_player_data()  # TODO: player listing

        self.menu = KezMenu(
            ["Arcade Mode", lambda: GameBoard().main(screen, self)],
            [self.player_name, self.update_player_name],
            ["Controls", lambda: setattr(self, "help", not self.help)],
            ["Reset Scores", self.reset_scores],
            ["Quit", lambda: setattr(self, 'running', False)],
        )
        # TODO: change this. should make a player screen where they can see
        #       what accounts have been made locally, what their stats are,
        #       what their upper limits are, rename them, cheat, etc...
        PLAYER_INDEX = 1  # index of the player's name

        self.menu.x = self.resolution[0] // 2.5
        self.menu.y = self.resolution[1] // 2
        self.menu.color = Blocks.rgba_codes["light_blue"]
        self.menu.focus_color = Blocks.rgba_codes["dark_pink"]

        background = load_image("background.png")
        render = lambda x: self.font.render(x, True, self.menu.color)
        render_red = lambda x: self.font.render(x, True, self.menu.focus_color)

        while self.running:
            events = pygame.event.get()

            if self.updating_name is True:
                events = self.handle_name_change(events)
            elif self.magic_enabled:
                for setting in self.magic_enabled:
                    events = self._handle_magic_change(events, setting)

            if self.player_name == self.default_name:
                menu_name = "{} -- Click to change".format(self.default_name)
            else:
                menu_name = self.player_name
            self.menu.options[PLAYER_INDEX]["label"] = menu_name

            self.handle_magic(events)
            self.menu.update(events or [], clock.tick(30) / 1000.0)
            screen.blit(background, (0, 0))

            # title text
            small = self.small_title.render("the tragedy of the", True,
                                            Blocks.rgba_codes["dark_pink"])
            small_size = self.small_title.size("the tragedy of the")
            screen.blit(small,
                        (self.resolution[0] // 2 - (small_size[0] // 2), 120))
            big = self.big_title.render("FALLING SKY", True,
                                        Blocks.rgba_codes["teal"])
            big_size = self.big_title.size("FALLING SKY")
            screen.blit(big,
                        (self.resolution[0] // 2 - (big_size[0] // 2), 150))

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
                control_size = (0, 0)
                for control in controls:
                    size = self.font.size(control)
                    if size[0] > control_size[0]:
                        control_size = size

                help_bg = pygame.Surface(
                    (
                        control_size[0] + 10,
                        ((control_size[1] + self.buffer) * (len(controls))
                         ) + 10,
                    ),
                    flags=pygame.SRCALPHA,
                )
                help_bg.fill((0, 0, 0, 150))
                screen.blit(help_bg, (
                    25,
                    self.resolution[1] - (
                        (control_size[1] + self.buffer) * (len(controls))
                    ) + 5
                ))

                for i, control in enumerate(controls):
                    screen.blit(render_red(control), (
                        30,
                        self.resolution[1] - (
                            (control_size[1] * (len(controls) + 1)) -
                            (i * control_size[1]) + self.buffer
                        )
                    ))

            if self.data["wins"] or self.data["losses"]:
                label = "{user_id} wins: {wins} losses: {losses}".format(
                    **self.data
                )
                win_loss = render(label)
                win_loss_size = self.font.size(label)
                screen.blit(win_loss, (
                    (self.resolution[0] / 2) - (win_loss_size[0] / 2),
                    self.buffer,
                ))

            if self.magical:
                self._magic_method()
            self.menu.draw(screen)
            pygame.display.flip()

    def _handle_keypress(self, events, keylist, cancel_list=None):
        """Handles keypresses into a list.

        Args::

            events: list from pygame.event.get()
            keylist: list to append/delete from on user input
            cancel_list: list to return to should the user cancel, or None

        Returns:
            Events not consumed, an empty list, or None on cancel
        """

        if cancel_list is None:
            cancel_list = keylist

        scrubbed_events = []
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == 27:  # esc/cancel
                    keylist = cancel_list
                    return None
                elif event.key in (92, 8):  # backspace(s)
                    keylist = keylist[:-1]
                elif event.key not in (13,) and len(keylist) <= 12:
                    # 13 == enter and 12 is some limit to name length
                    try:
                        key = chr(event.key)
                    except ValueError:
                        if event.key not in range(273, 277):
                            scrubbed_events.append(event)
                    else:
                        if pygame.key.get_mods() in (1, 4097, 8192, 12288):
                            # checks for shift or caps lock, and both
                            key = key.capitalize()
                        keylist += key
                else:
                    scrubbed_events.append(event)
            else:
                scrubbed_events.append(event)

        return scrubbed_events, keylist

    def handle_name_change(self, events):
        """Proccess events during a name change."""

        events, player_name = self._handle_keypress(
            events,
            self.player_name,
            self._old_player_name,
        )
        self.player_name = player_name
        if events is None:
            self.update_player_name()
            return []
        else:
            return events

    def _handle_magic_change(self, events, keylist):
        if not events:
            return
        events, updated = self._handle_keypress(
            events,
            keylist=self.data.data[keylist],
            cancel_list=self.data.data["old_{}".format(keylist)],
        )
        self.data[keylist] = updated
        return events or []

    def _magic_width(self):
        self._magic_int_change("width")

    def _magic_height(self):
        self._magic_int_change("height")

    def _magic_nexts(self):
        self._magic_int_change("nexts")

    def _magic_blocksize(self):
        self._magic_int_change("blocksize")

    def _magic_fallrate(self):
        self._magic_int_change("fallrate")

    def _magic_bonus_block_rate(self):
        self._magic_int_change("bonus_block_rate")

    def _magic_int_change(self, key):
        if not "old_{}".format(key) in self.data:
            self.data["old_{}".format(key)] = self.data[key]
            self.magic_enabled.append(key)
            self.data[key] = ""
        else:
            old_setting = self.data.pop("old_{}".format(key))
            try:
                self.data[key] = int(self.data[key])
            except:
                self.data[key] = old_setting
            self.data.save()
            self.magic_enabled = []

    def _magic_spawn_rate(self):
        key = "spawn_rate"
        self.data[key] = not self.data[key]
        self.data.save()

    def _magic_method(self):
        """Just checks the time."""

        if not hasattr(self, "_magic_init"):
            self._magic_init = True
            for key in sorted(self.magic_available, key=len):
                self.menu.options.append({
                    "label": "{}: {}".format(key, self.data[key]),
                    "callable": getattr(self, "_magic_{}".format(key)),
                })
        else:
            for key, val in self.data.items():
                for option in self.menu.options:
                    if option["label"].startswith(key):
                        option["label"] = "{}: {}".format(key, val)
                        break

    def handle_magic(self, events):
        """Doesn't do anything."""

        for e in events or []:
            if e.type == 2:
                self.magic.append(e.key)
                for i, q in zip(self.magic, self.magic_sequence):
                    if i != q:
                        self.magic = []
                        break
                else:
                    if len(self.magic) == len(self.magic_sequence):
                        self.magical = True

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
