"""Shape object for The Tragedy of the Falling Sky.

Movement handling to the child blocks happens here.
"""


from __future__ import division

import pygame
import random

from fallingsky.block import Block
from fallingsky.util import Coord


IMADEVELOPER = False


class Shapes(object):
    """A lazymans enum to represent the block types and their IDs."""

    all_types = {
        0: "l",
        1: "s",
        2: "z",
        3: "i",
        4: "o",
        5: "j",
        6: "t",
    }

    def __init__(self):
        for id_, type_ in Shapes.all_types.items():
            setattr(self, type_, id_)

    @staticmethod
    def get_type(block_type_int):
        return Shapes.all_types.get(block_type_int)


class Shape(object):
    """Creates a shape as per the BlockTypes enum.

    Init args::

        game: the GameBoard object
        centre_px: integer pixel that is the centre of the window
        shape: integer shape ID to force a shape, or None for random selection
        blocksize: integer block width and height in pixels
        groups
    """

    def __init__(self, game, position=0, shape=None, visible=True):
        if shape is None:
            self.shape = 3 if IMADEVELOPER else not_so_random_shape(game)
        else:
            self.shape = shape

        game.history[self.shape] += 1

        self.shape_name = Shapes.get_type(self.shape)
        self.position = position

        bs = game.blocksize
        offset_coords = {
            "l": [(-bs, 0), (0, 0), (bs, 0), (bs, -bs)],
            "j": [(-bs, -bs), (-bs, 0), (0, 0), (bs, 0)],
            "s": [(bs, -bs), (0, -bs), (0, 0), (-bs, 0)],
            "z": [(-bs, -bs), (0, -bs), (0, 0), (bs, 0)],
            "t": [(0, -bs), (-bs, 0), (0, 0), (bs, 0)],
            "o": [(-bs, -bs), (0, -bs), (0, 0), (-bs, 0)],
            "i": [(-(bs * 2), 0), (-bs, 0), (0, 0), (bs, 0)],
        }

        self.offset_coords = offset_coords[self.shape_name]
        self.initial_offset = self.offset_coords
        self.vertical_offset = game.vertical_offset + (game.blocksize * (
            1 + int(self.shape_name != "i")
        ))
        self.exploding = False
        self.falling = True
        self.fall_rate = max(1100 - (game.fallrate * 50), 65)
        self.next_fall = self.fall_rate
        self.move_rate = 100
        self.next_move = self.move_rate
        self.turn_rate = 200
        self.next_turn = self.turn_rate
        self.down_rate = 100  # need to throttle down to encourage slams
        self.down_available = self.down_rate
        self.blocks = []
        self.bottom_mercy = 1  # mercy/grace ticks for bottom stickyness

        if self.position == 0:
            # this can return False, but we don't really care right now
            block_positions = self.can_activate(game) or []
        else:
            block_positions = self._locations_in_queue(game)

        for location in block_positions:
            self.blocks.append(Block(location, self.shape_name, 0, game,
                                     game.sprites, visible=visible))

        self.shadow_blocks = []

        # spawn our shawdows if we're spawning as an active shape
        if self.position == 0 and block_positions:
            self.spawn_shadow_blocks(game)

    def spawn_shadow_blocks(self, game):
        """Builds the coords for shadows based off of self.blocks.

        Args:
            game: the GameBoard object

        Returns:
            None, appends Block objects of shadow type to self.shadow_blocks
        """

        for coord in self._shadow_coords(game):
            self.shadow_blocks.append(
                Block(coord, "shadow", 0, game, game.sprites)
            )

    def _shadow_coords(self, game):
        """Determine the coords for the shadow of this shape.

        The shadow is always directly downwards from the shape.

        Returns:
            list of coords in order of self.shadow_blocks
        """

        # self.blocks exists at this point, is active, and can abuse the coords
        shadow_blocks = [(block.rect.x, block.rect.y) for block in self.blocks]
        game_coords = [block["coord"] for block in game.blocks]
        think_of_the_bits = game.height * 2
        finished = False
        while not finished and think_of_the_bits > 0:
            think_of_the_bits -= 1
            shadow_blocks_next = []
            for block in shadow_blocks:
                new_coord = (block[0], block[1] + game.blocksize)
                if new_coord in game_coords:
                    finished = True  # double break
                    break
                else:
                    shadow_blocks_next.append(new_coord)
            else:
                shadow_blocks = shadow_blocks_next

        return shadow_blocks if think_of_the_bits > 0 else []

    def move_closer(self, game):
        """Move to the next closest position in the next waiting area."""

        self.position -= 1
        for coord, block in zip(self._locations_in_queue(game), self.blocks):
            block.rect.x = coord[0]
            block.rect.y = coord[1]

    def _locations_in_queue(self, game):
        """Returns the block coords for the integer position in the queue.

        Args::

            game: the GameBoard object spawning us
            position: an integer position (1-10?) of our place in queue
        """

        # TODO: rows & better placement
        block_positions = []
        right_shift = (((game.width // 2) + 4) * game.blocksize)
        down_shift = (((self.position - 1) * 3) * game.blocksize)
        for block_offset in self.offset_coords:
            location = (
                game.centre_px + block_offset[0] + right_shift,
                self.vertical_offset + block_offset[1] + down_shift,
            )
            block_positions.append(location)

        return block_positions

    def become_held(self, game):
        """Move this shape to the hold area."""

        self.offset_coords = self.initial_offset
        block_positions = []
        right_shift = (((game.width // 2) + 4) * game.blocksize)
        for block_offset in self.offset_coords:
            location = (
                game.centre_px + block_offset[0] - right_shift,
                self.vertical_offset + block_offset[1],
            )
            block_positions.append(location)

        for coord, block in zip(block_positions, self.blocks):
            block.rect.x = coord[0]
            block.rect.y = coord[1]

        for block in self.shadow_blocks:
            block.explode(game)
        self.shadow_blocks = []
        self.falling = False

    def make_active(self, game):
        """Move this shape from the next or hold areas to the active area.

        Args:
            game: the GameBoard object spawning us

        Returns:
            boolean of succesfully becoming active
        """

        move_locations = self.can_activate(game)
        if move_locations:
            for coords, block in zip(move_locations, self.blocks):
                block.rect.x = coords[0]
                block.rect.y = coords[1]
                block.visible = True
            self.spawn_shadow_blocks(game)
            self.falling = True
            self.fall_rate = max(1100 - (game.fallrate * 50), 65)
            self.next_fall = self.fall_rate
            return True
        else:
            return False

    def can_activate(self, game):
        """Checks if we can become the active block. Can set game.active = 0.

        Returns:
            list of positions to move self.blocks to or False if not possible
        """

        move_locations = []
        game_coords = [block["coord"] for block in game.blocks]
        for block_offset in self.offset_coords:
            location = Coord(
                game.centre_px + block_offset[0],
                self.vertical_offset + block_offset[1],
            )
            if location in game_coords:
                game.active = 0
                self.falling = False
                return False
            else:
                move_locations.append(location)

        return move_locations

    def _move_coords(self, game, coords, game_coords, left=False, right=False,
                     down=False):
        """Determins the coordinates possible to move from coords in direction.

        Args::

            game: GameBoard object which requested this Shape
            coords: tuple of (x, y) coordinates currently at
            game_coords: list of tuple of collidable blocks in play
            left: boolean to request leftbound movement
            right: boolean to request rightward movement
            down: boolean to request movement downwards

        Returns:
            tuple of coords (x, y), updated for the move if no collision
        """

        if left:
            desired_coords = Coord(coords[0] - game.blocksize, coords[1])
        elif right:
            desired_coords = Coord(coords[0] + game.blocksize, coords[1])
        elif down:
            desired_coords = Coord(coords[0], coords[1] + game.blocksize)

        return coords if desired_coords in game_coords else desired_coords

    def _move_blocks(self, game, left=False, right=False, down=False):
        """Moves all the blocks in self.blocks the direction asked."""

        block_moves = []
        game_coords = [block["coord"] for block in game.blocks]
        for block in self.blocks:
            coords = Coord(block.rect.x, block.rect.y)
            new_coords = self._move_coords(game, coords, game_coords, left,
                                           right, down)
            if coords == new_coords:
                if down:
                    if self.bottom_mercy > 0:  # mercy granted, this time
                        self.bottom_mercy -= 1
                        return False

                    # we've hit ground, add coords and block to game.blocks
                    for block, shadow in zip(self.blocks, self.shadow_blocks):
                        game.blocks.append({
                            "coord": Coord(block.rect.x, block.rect.y),
                            "sprite": block,
                        })
                        shadow.explode(game)

                    self.shadow_blocks = []
                    self.falling = False
                return False  # cancels the move, new_coords are not new
            else:
                block_moves.append(new_coords)

        # move the regular blocks
        for block, new_coords in zip(self.blocks, block_moves):
            block.rect.x = new_coords[0]
            block.rect.y = new_coords[1]

        self._update_shadow_positions(game)
        return True

    def _update_shadow_positions(self, game):
        """Moves the shadow blocks after a block move or rotate."""

        for block, coord in zip(self.shadow_blocks, self._shadow_coords(game)):
            block.rect.x = coord[0]
            block.rect.y = coord[1]

    def slam_blocks(self, game):
        """Moves all blocks as far down as possible."""

        for shadow in self.shadow_blocks:
            shadow.explode(game)
        self.shadow_blocks = []

        game_coords = [block["coord"] for block in game.blocks]

        # we may be unable to move downwards, when slamming while losing
        for block in self.blocks:
            coords = Coord(block.rect.x, block.rect.y)
            new_coord = self._move_coords(game, coords, game_coords, down=True)
            if new_coord == coords:
                # we're done moving, make us colliadable
                desired_coords = None
                break
        else:
            desired_coords = self._shadow_coords(game)

        if desired_coords:
            for block, coords in zip(self.blocks, desired_coords):
                block.rect.x, block.rect.y = coords[0], coords[1]

        for block in self.blocks:
            game.blocks.append({
                "coord": Coord(block.rect.x, block.rect.y),
                "sprite": block,
            })

        self.falling = False

    def _rotate_blocks(self, game, clockwise=True, retry=0):
        """Rotate the blocks in the shape in a direction if possible.

        Args:
            game: the GameBoard object which spawned this Shape object
            clockwise: boolean to rotate clockwise or counter-clockwise
            retry: boolean of if this function is being recalled after shifting

        Returns:
            boolean of if the block rotated
        """

        if self.shape_name == "o":
            return False  # square blocks don't rotate...

        requested_movements = []
        game_coords = [block["coord"] for block in game.blocks]
        centre = (self.blocks[2].rect.x, self.blocks[2].rect.y)
        for offset, block in zip(self.offset_coords, self.blocks):
            if clockwise:
                move_offset = ((-1 * offset[1]), offset[0])
            else:
                move_offset = (offset[1], (-1 * offset[0]))

            requested_move = Coord(
                centre[0] + move_offset[0],
                centre[1] + move_offset[1],
            )
            if requested_move in game_coords:
                if requested_move in game.walls and retry <= 2:
                    return self._shift_retry_rotate(game, clockwise, retry)
                else:
                    return False
            else:
                requested_movements.append(requested_move)

        for requested_move, block in zip(requested_movements, self.blocks):
            block.rect.x = requested_move[0]
            block.rect.y = requested_move[1]

        self._rotate_offsets(clockwise)
        self._update_shadow_positions(game)
        return True

    def _block_locations(self):
        """Returns the current block locations in a list of coord tuples."""

        return [(block.rect.x, block.rect.y) for block in self.blocks]

    def _shift_retry_rotate(self, game, clockwise, retry=0):
        """Shift the blocks away from the walls and try to rotate again."""

        retry += 1
        start_coords = self._block_locations()

        if start_coords[0][0] > game.centre_px:  # first block, x coord
            moved = self._move_blocks(game, left=True)
        else:
            moved = self._move_blocks(game, right=True)

        rotated = False
        if moved:
            rotated = self._rotate_blocks(game, clockwise, retry)

        if rotated:
            return True

        else:
            for block, coord in zip(self.blocks, start_coords):
                block.rect.x = coord[0]
                block.rect.y = coord[1]
            return False

    def _rotate_offsets(self, clockwise=True):
        """Updates self.offsets with a rotation factor."""

        new_offsets = []
        for offset in self.offset_coords:
            if clockwise:
                new_offsets.append(((-1 * offset[1]), offset[0]))
            else:
                new_offsets.append((offset[1], (-1 * offset[0])))
        self.offset_coords = new_offsets

    def update(self, dt, game, key_presses):
        """Called per clock tick. Controls user input for shape movement."""

        if self.falling:

            self.next_fall -= dt
            self.next_move -= dt
            self.next_turn -= dt
            self.down_available -= dt

            for key in key_presses:
                self.handle_key_press(game, key)

            if self.next_fall < 0:
                self._move_blocks(game, down=True)
                self.next_fall = self.fall_rate

            # show or hide shadow blocks if we're colliding with them
            block_locations = self._block_locations()
            for shadow in self.shadow_blocks:
                if (shadow.rect.x, shadow.rect.y) in block_locations:
                    shadow.visible = False
                else:
                    shadow.visible = True

    def handle_key_press(self, game, key):
        """Logic per key press.

        Returns:
            boolean of if the shadow blocks need to be updated or not
        """

        # TODO: make a player-friendly mode to reset mercy on every move/turn

        # falling sped up
        if key in (pygame.K_DOWN, pygame.K_s) and self.down_available <= 0:
            self._move_blocks(game, down=True)
            self.down_available = self.down_rate
            self.next_fall = self.fall_rate
            return False

        # right and left
        elif key in (pygame.K_LEFT, pygame.K_a) and self.next_move <= 0:
            self._move_blocks(game, left=True)
            self.next_move = self.move_rate
        elif key in (pygame.K_RIGHT, pygame.K_d) and self.next_move <= 0:
            self._move_blocks(game, right=True)
            self.next_move = self.move_rate

        # rotate, both directions
        elif key in (pygame.K_UP, pygame.K_e, pygame.K_w) and \
                self.next_turn <= 0:
            self._rotate_blocks(game)
            self.next_turn = self.turn_rate
        elif key in (pygame.K_q,) and self.next_turn <= 0:
            self._rotate_blocks(game, clockwise=False)
            self.next_turn = self.turn_rate


def not_so_random_shape(game):
    """Used to determine the next shape ID. Tries to weigh the odds evenly."""

    roll_for_shape = lambda: random.sample(game.history.keys(), 1)[0]
    shape_id = roll_for_shape()
    shapes_spawned = sum(game.history.values())

    if shapes_spawned > 4:
        shape_spawn_rate = lambda x: game.history[x] / shapes_spawned
        while shape_spawn_rate(shape_id) > 1 / (len(game.history) - 1):
            shape_id = roll_for_shape()

    return shape_id
