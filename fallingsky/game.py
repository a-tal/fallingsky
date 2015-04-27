"""The Tragedy of the Falling Sky's main game loop."""


from __future__ import division

import os
import pygame
import random
import tempfile

from collections import Counter
from collections import namedtuple
from collections import defaultdict

from fallingsky import __version__
from fallingsky.block import Block
from fallingsky.score import Keeper
from fallingsky.shapes import Shape
from fallingsky.shapes import Shapes
from fallingsky.user import UserData
from fallingsky.util import load_image
# from fallingsky.util import load_sound
from fallingsky.walls import arcade_mode


class GameBoard(object):
    """Main game object, passed to other classes instantiated as `game`.

    Controls main logic for a level of gameplay, spawning Sprite classes.

    Initialized with no arguments. (init isn't important)

    GameBoard.main() is the method called per level, which interacts with the
    game menu object defined further below.
    """

    def __init__(self):
        self.fonts = {
            "large": pygame.font.SysFont("arial", 64),
            "normal": pygame.font.SysFont("arial", 28),
            "small": pygame.font.SysFont("courier new", 8),
        }
        self.score = Keeper()
        self.lines = 0
        self.paused = False

    def render(self, text, font="normal", color=None, background=None):
        """Uses pygame's font.render to make some text.

        Args::

            test: string text to render
            font: string key font name in self.fonts
            color: a tree integer tuple RGB color code, or white

        Returns:
            font object to blit somewhere
        """

        return self.fonts[font].render(text, True, color or (255, 255, 255),
                                       background)

    def refresh_background(self, dt):
        """Called per clock cycle, updates all graphics."""

        self.screen.fill((111, 111, 111))  # TODO: make better

        # go through the game sprites and update/reblit them if visible
        for sprite in self.sprites:
            sprite.update(dt, self)
            if sprite.visible:
                self.screen.blit(sprite.image, (sprite.rect.x, sprite.rect.y))

        # grab some current game stats
        stats = [
            self.render("level: {}".format(self.fallrate)),
            self.render("lines: {:,}".format(self.lines)),
            self.render("game: {:,}".format(int(self.score.game))),
        ]

        if self.score.total:  # only after the first loss
            stats.append(self.render("total: {:,}".format(self.score.total)))

        if self.score.best != self.score.total:  # after 2nd loss
            stats.append(self.render(
                "best: {:,}".format(int(self.score.best))
            ))

        if self.bonus_blocks:  # once they get 100k points
            stats.append(self.render("bonus: {:,}".format(sum([
                self.blocks[coord].bonus_points for coord in self.bonus_blocks
            ]))))
        elif self.bonus_block_rate:
            stats.append(self.render(
                "{} complete!".format(self.bonus_block_rate)
            ))
        elif self.score.game.get_score() > 100000:
            stats.append(self.render("!"))  # just a small notification ...

        if self.show_shape_spawn_rate:  # debug/info option
            shapes_spawned = sum(self.history.values())
            shape_spawn_rate = lambda x : self.history[x] / shapes_spawned
            stats.append(self.render(""))  # spacer
            stats.extend([self.render("{}: {:.2%}".format(
                Shapes.all_types[shape].title(),
                shape_spawn_rate(shape)
            )) for shape in self.history])

        for i, stat in enumerate(stats):  # draw the rendered fonts on screen
            self.screen.blit(stat, (60, 30 + (i * 30)))

        # display name and version
        self.screen.blit(
            self.render(
                "The Tragedy of the Falling Sky v{}".format(__version__),
                font="small",
                color=(0, 0, 0),
            ),
            (5, self.resolution[1] - 10),  # bottom left corner
        )

        # let the user know if we're paused
        if self.paused:
            label = "    PAUSED    "
            paused = self.render(
                label,
                font="large",
                background=(0, 0, 0),
            )
            paused_size = self.fonts["large"].size(label)
            self.screen.blit(
                paused,
                ((self.resolution[0] / 2) - (paused_size[0] / 2),
                 (self.resolution[1] / 2) - (paused_size[1] / 2)),
            )

        pygame.display.flip()   # flip and we're done for this update

    def reset_blocks(self):
        """Resets self.blocks to a dict of {coords: None} for the walls."""

        self.blocks = {coord: None for coord in self.walls}
        for sprite in self.sprites:
            if hasattr(sprite, "explode"):
                sprite.explode(self)

        # respawn the walls
        for coord in self.wall_coords:
            Block(coord, "wall", 0, self, self.sprites)

        # shape history, used by shapes when spawning
        self.history = Counter({key: 0 for key in Shapes.all_types.keys()})
        self.spawn_bonus_blocks()

    def explode_full_lines(self):
        """Explodes all fully filled lines. Updates self.lines and game score.

        Returns:
            Integer count of the number of lines destroyed.
        """

        blocks_per_line = Counter()
        blocks_by_line = defaultdict(list)

        for coords, block in self.blocks.items():
            if block is not None:
                blocks_per_line[coords[1]] += 1
                blocks_by_line[coords[1]].append(block)

        destroyed_lines = []
        for line, count in blocks_per_line.items():
            if count >= self.width:
                destroyed_lines.append(line)

        # add the score /before/ exploding any blocks so the multipliers work
        num_lines_destroyed = len(destroyed_lines)
        points = int(
            ((num_lines_destroyed ** 1.5) * (100 * self.width) // 500) * 500
        )
        self.score.game += points

        # track lines, adjust the fallrate maybe
        self.lines += num_lines_destroyed
        self.lines_until_speed_up -= num_lines_destroyed
        if self.lines_until_speed_up <= 0 and self.fallrate < self.max_level:
            self.fallrate += 1
            self.lines_until_speed_up = self.lines_per_level

        # explode all the full lines, remove them from self.blocks
        for line in destroyed_lines:
            for block in blocks_by_line[line]:
                blk = self.blocks.pop((block.rect.x, block.rect.y))
                blk.explode(self)

        destroyed_lines = sorted(destroyed_lines)

        if destroyed_lines:  # this call is expensive and recursive
            num_lines_destroyed += self.blocks_fall_down(destroyed_lines)

        return num_lines_destroyed

    def _get_blocks_to_move(self, destroyed_lines):
        """Determines the lines connected to the destroyed lines.

        Returns:
            dictionary of line num: list of moved block sprites in that line
        """

        connected_lines = list(destroyed_lines)
        moved_blocks = defaultdict(list)

        line = connected_lines[0]
        line_found = True
        while line_found:  # check up
            line -= self.blocksize

            if line in connected_lines:
                continue

            line_found = False
            for coords, block in self.blocks.items():
                if coords[1] == line and block:
                    if line not in connected_lines:
                        connected_lines.append(line)
                        line_found = True
                    moved_blocks[line].append((coords, block))

        return moved_blocks

    def blocks_fall_down(self, destroyed_lines):
        """Moves the rest of the board downwards for the destroyed lines."""

        moved_blocks = self._get_blocks_to_move(destroyed_lines)
        colliders = list(self.bonus_blocks)

        for _ in range(len(destroyed_lines)):
            moved_this_loop = defaultdict(list)

            for line, blocks in reversed(sorted(moved_blocks.items())):
                for coord, block in blocks:
                    if block is None or block.bonus_points:
                        moved_this_loop[line].append((coord, block))
                    else:
                        # clean up current position if we're moving down multiple lines
                        if coord in colliders:
                            colliders.remove(coord)
                        desired_move = (coord[0], coord[1] + self.blocksize)
                        if desired_move in colliders:
                            colliders.append(coord)
                        else:
                            colliders.append(desired_move)
                            blk = self.blocks.pop(coord, None)
                            if blk:
                                blk.rect.y += self.blocksize
                                self.blocks[(blk.rect.x, blk.rect.y)] = blk

                        moved_this_loop[line].append((
                            (block.rect.x, block.rect.y), block
                        ))

            moved_blocks = moved_this_loop

        # it is possible that we've moved down to make another full line
        return self.explode_full_lines()

    def spawn_bonus_blocks(self):
        """Spawns bonus blocks inside the game grid."""

        self.bonus_blocks = []

        # give them some room up top (still low odds to spawn here)
        max_spawn_height = self.height - 2

        # this is pretty much standard deviation, but with /no/ outliers
        odds = {"big": 342, "mid": 137, "sml": 21}  # HACK: keys are important
        range_distribution = {key: 0 for key in odds}

        # count bonus block spawns above and below the mean
        row_distribution = {key: Counter(above=0, below=0) for key in odds}

        # mean is at a ratio of 1:3 compared to the max height
        mean = max_spawn_height // 3

        # the standard deviation length is at a ratio of 1:7 of the max height
        std = max_spawn_height // 7

        rows_above = lambda x : list(range(
            max(mean - (std * x), 0),
            max(mean - (std * (x - 1)), 0)
        ))
        rows_below = lambda x : list(range(
            min(mean + (std * x) - std, max_spawn_height),
            min(mean + (std * (x + 1)) - std, max_spawn_height)
        ))
        Rows = namedtuple("Rows", ("above", "below"))
        row_range = lambda x : Rows(below=rows_below(x), above=rows_above(x))
        # HACK: using the key names sorted here, don't change odds' keys ;)
        rows = {key: row_range(i) for i, key in enumerate(sorted(odds), 1)}

        # fucky int: int dict to track what rows to spawn bonus blocks in
        row_spawns = {row: 0 for row in range(max_spawn_height)}

        # track each column in each row for spawning inside of
        row_columns = {
            row: list(range(-int(self.width / 2), int(self.width / 2))) for \
                row in range(max_spawn_height)
        }

        for _ in range(self.bonus_block_rate):

            rolls_so_far = sum(range_distribution.values())
            while True:
                # roll and determine the odds section it landed in
                roll = random.randint(0, 1000)
                if roll < odds["sml"] * 2:
                    section = "sml"
                    if range_distribution["sml"] and rolls_so_far < 10:
                        continue  # getting this way too often, shortcut
                elif roll < odds["mid"] * 2:
                    section = "mid"
                else:
                    section = "big"

                # apply some logic to smooth out the distribution
                if rolls_so_far > 2 and range_distribution[section] and \
                        range_distribution[section] / (rolls_so_far + 1) > \
                        ((odds[section] + ((1/5) * odds[section])) * 2) / 1000:
                    continue
                else:
                    break

            range_distribution[section] += 1

            above = random.randint(0, 1)

            # move above/below into the lesser populated area
            dist = row_distribution[section]
            if (dist["above"] and above and dist["above"] > dist["below"]) or \
               (dist["below"] and not above and dist["below"] > dist["above"]):
                above = 0 if above else 1

            def available_rows():
                return [row for row in rows[section][above] if \
                        row_spawns[row] < self.width - 1]

            this_row = None
            try:
                this_row = random.sample(available_rows(), 1)[0]
            except ValueError:
                above = 0 if above else 1  # swap value
                try:
                    this_row = random.sample(available_rows(), 1)[0]
                except ValueError:
                    # so many bonus blocks we've filled the distribution area
                    # ignored, but accept it statistically to spawn other areas
                    pass
            finally:
                row_spawns[this_row] += 1

            if above:
                row_distribution[section]["above"] += 1
            else:
                row_distribution[section]["below"] += 1

            column = random.sample(row_columns[this_row], 1)[0]
            row_columns[this_row].remove(column)
            level = random.randint(3, 5)
            location = (
                self.centre_px + (column * self.blocksize),
                self.vertical_offset + ((self.height - this_row - 3) * self.blocksize)
            )
            self.spawn_bonus_block(location, level)

    def spawn_bonus_block(self, location, level):
        """Creates a bonus block at location and bonus level."""

        self.blocks[location] = Block(
            location,
            "bonus_{}".format(level),
            level,
            self,
            self.sprites,
        )
        if location not in self.bonus_blocks:
            self.bonus_blocks.append(location)

    def reset_game_board(self):
        """Explodes everything and resets the gameboard."""

        # explode the board
        for _, block in self.blocks.items():
            if block is not None:
                block.bonus_points = 0
                block.explode(self)

        # explode the next queue
        for shape in self.next_queue:
            for block in shape.blocks:
                block.explode(self)

        # reset let's play again!
        # TODO: add screens/gameplay here
        self.score.game_over()
        self.reset_blocks()
        self.lines = 0
        self.next_queue = [
            Shape(game=self, position=i) for i in range(1, self.nexts)
        ]
        self.active = True
        self.fallrate = self.starting_fallrate

    def get_next_shape(self):
        """Gets the next-in-line shape from self.next_queue.

        Moves forward all other members and spawns a new one at the end.
        """

        new_shape = self.next_queue.pop(0)
        for next_shape in self.next_queue:
            next_shape.move_closer(self)
        self.next_queue.append(
            Shape(game=self, position=self.nexts - 1)
        )
        return new_shape

    def end_game(self, menu):
        """Ends the game, updates the scores in the menu.data object."""

        game_score = self.score.game.get_score()
        if not isinstance(self.active, bool) and self.active > 0 or \
                (not self.bonus_blocks and self.bonus_block_rate) or \
                (not self.bonus_block_rate and game_score > 50000) or \
                game_score > 100000:
            menu.data["wins"] += 1
            menu.data["bonus_block_rate"] += 1
            self.bonus_block_rate += 1
        else:
            menu.data["losses"] += 1

        menu.data["total_score"] += game_score
        menu.data["best_score"] = max(menu.data["best_score"], game_score)
        menu.data.save()

    def main(self, screen, menu):
        """Main Game routine. Make fun now! :D

        Args::

            screen: the PyGame screen object we're running inside
            menu: MainMenu object which called us
        """

        # grab a clock so we can limit and measure the passing of time
        clock = pygame.time.Clock()

        # TODO: make a real background
        # background = load_image("background.png")

        self.screen = screen
        self.resolution = menu.resolution
        self.blocksize = min(menu.data["blocksize"], 12) * 4

        # board size
        max_width = int(menu.resolution[0] / self.blocksize) - 10
        max_height = int(menu.resolution[1] / self.blocksize) - 3
        self.width = min(menu.data["width"], max_width)
        self.height = min(menu.data["height"], max_height)

        # speed
        self.fallrate = menu.data["fallrate"]
        self.starting_fallrate = self.fallrate

        # score
        self.score.resume(menu.data["total_score"], menu.data["best_score"])
        self.bonus_block_rate = menu.data["bonus_block_rate"]

        # "features"
        self.nexts = menu.data["nexts"] + 1  # plus 1 because of range usage
        self.show_shape_spawn_rate = menu.data["show_shape_spawn_rate"]

        # do geometry, generate the xml map
        self.centre_px = int(
            ((self.resolution[0] / self.blocksize) / 2) * self.blocksize
        )
        self.vertical_offset = int(
            ((self.resolution[1] // self.blocksize) - self.height) * self.blocksize
        )
        self.walls, self.wall_coords = arcade_mode(
            resolution=self.resolution,
            blocksize = self.blocksize,
            width=self.width,
            height=self.height,
        )

        # create a SpriteLayer for all our sprites to live in
        self.sprites = pygame.sprite.AbstractGroup()

        # spawn the walls, reset blocks
        self.reset_blocks()

        # this board will remain active until a Shape class toggles it False
        # when it finds it collides when placing itself on the board
        self.active = True

        # build initial shapes here
        current_shape = Shape(game=self)

        # TODO: display next shapes as per skill level
        # just by ID though, don't spawn them as Shape objects, or change Shape
        # init to maybe display into a "next" box of varying length
        self.next_queue = [
            Shape(game=self, position=i) for i in range(1, self.nexts)
        ]
        swappped = False
        swapped_shape = None
        # TODO: move these constants somewhere common
        self.max_level = 21
        self.lines_per_level = 8 # 16  # XXX
        self.lines_until_speed_up = self.lines_per_level
        slam_delay = 200
        slam_available = slam_delay
        swap_delay = 400
        swap_available = swap_delay

        while True:
            # limit updates to 30 times per second and determine how much time
            # passed since the last update
            dt = clock.tick(60)
            slam_available -= dt
            swap_available -= dt
            # handle basic game events; terminate this main loop if the window
            # is closed or the escape key is pressed

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.end_game(menu)
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.end_game(menu)
                        return
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused

            if self.paused:
                keys = []
            else:
                keys = [i for i, k in enumerate(pygame.key.get_pressed()) if k]

            nuke_keys = False
            for key in keys:
                # swap
                if key in (pygame.K_x, pygame.K_h) and swap_available < 0 and \
                        not swappped and current_shape.falling:
                    swap_available = swap_delay
                    current_shape.become_held(self)
                    current_shape, swapped_shape = swapped_shape, current_shape
                    nuke_keys = True

                    if current_shape is None:
                        # first move to the hold area, grab next in line
                        current_shape = self.get_next_shape()
                    else:
                        swappped = True

                    if current_shape.can_activate(self):
                        current_shape.make_active(self)

                # slam
                elif key in (pygame.K_SPACE,) and slam_available < 0:
                    current_shape.slam_blocks(self)
                    nuke_keys = True

            if self.active and not self.paused:
                current_shape.update(dt, self, [] if nuke_keys else keys)

            self.refresh_background(dt) #, background)

            if self.active is not True:  # changes from True to int win/loss
                self.end_game(menu)
                self.reset_game_board()
                current_shape = self.get_next_shape()
                current_shape.make_active(self)
                if swapped_shape:
                    for block in swapped_shape.blocks:
                        block.explode(self)
                    del swapped_shape
                    swapped_shape = None
                slam_available = slam_delay
                swap_available = swap_delay
                continue

            if not current_shape.falling:  # the current shape stopped falling
                del current_shape
                destroyed_lines = self.explode_full_lines()
                if destroyed_lines:
                    pass  # play a sound here
                current_shape = self.get_next_shape()
                current_shape.make_active(self)
                swappped = False
                slam_available = slam_delay
                swap_available = swap_delay


class SoundEffects(object):
    """TODO: add sound :)"""

    pass
