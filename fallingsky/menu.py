# coding: utf-8
"""Holds the MainMenu object and between-game interaction."""


from __future__ import unicode_literals

import pygame
from kezmenu import KezMenu

from fallingsky.game import GameBoard
from fallingsky.user import UserData
# from fallingsky.util import load_image


class MainMenu(object):
    """The Main menu object class which contains all children.

    Initialized with the screen resolution as an (x, y) tuple
    """

    def __init__(self, resolution, *args, **kwargs):
        self.resolution = resolution
        self.running = True
        self.injected = False
        self.updating_name = False
        self.help = False
        self.font = pygame.font.SysFont("arial", 20)
        super(MainMenu, self).__init__(*args, **kwargs)

    def run_forever(self):
        """Maybe not quite forever, but until the user quits."""

        # start the screen object
        screen = pygame.display.set_mode(self.resolution)

        self.player_name = "Player 1"  # TODO: ID auto lookup/registration
        self.data = UserData(self.player_name)

        clock = pygame.time.Clock()
        # background = load_image("background.png")

        self.menu = KezMenu(
            ["Arcade Mode", lambda: GameBoard().main(screen, self)],
            [self.player_name, self.update_player_name],
            ["Controls", lambda : setattr(self, "help", not self.help)],
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

            self.menu.options[PLAYER_INDEX]["label"] = self.player_name

            self.menu.update(events, clock.tick(30) / 1000.0)
            screen.fill((99, 99, 99))  # TODO: make better
            # screen.blit(background, (0, 0))

            if self.help:
                # add controls/help to bottom
                controls = [
                    # render("-- Controls --"),
                    render("left: ← or A"),
                    render("right: → or D"),
                    render("down: ↓ or S"),
                    render("rotate clockwise: ↑, W, or E"),
                    render("rotate counter-clockwise: Q"),
                    render("hold/swap: H"),
                    render("slam down: space bar"),
                ]

                for i, control in enumerate(controls):
                    screen.blit(control, (self.resolution[0] - 275,
                                          self.resolution[1] - 200 + (i * 25)))

            self.menu.draw(screen)
            pygame.display.flip()
            if self.data["wins"] or self.data["losses"]:
                label = "wins: {wins} losses: {losses}".format(**self.data.data)
                if not self.injected:
                    self.injected = True
                    self.menu.options.append(
                        {"label": label, "callable": lambda : 1}
                    )
                else:
                    for option in self.menu.options:
                        if option["label"].startswith("wins: "):
                            option["label"] = label
                            break

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
            self.updating_name = False
            if not self.player_name:  # pressing enter twice, no input, cancels
                self.player_name = self._old_player_name
                return
            self._old_player_name = None
            self.menu.mouse_enabled = True
            self.data = UserData(self.player_name)
            if self.injected:
                self.menu.options.pop(-1)
                self.injected = False
        else:
            self.updating_name = True
            self._old_player_name = self.player_name  # save this for cancel
            self.player_name = ""
            self.menu.mouse_enabled = False
