"""Block logic.

Shapes are composed of many blocks while they are falling.
Once they have finished falling, they become independant.
"""


from __future__ import division

import pygame
import struct
from collections import namedtuple

from fallingsky.score import Keeper


class Blocks(object):
    rgba_codes = {  # name: (R, G, B, A)
        "black": (0, 0, 0, 255),
        "blue": (0, 87, 132, 255),
        "bonus_blue": (13, 27, 209, 180),
        "bonus_blue_alpha": (13, 27, 209, 80),
        "bonus_green": (56, 241, 6, 180),
        "bonus_green_alpha": (56, 241, 6, 80),
        "bonus_orange": (240, 120, 6, 180),
        "bonus_orange_alpha": (240, 120, 6, 80),
        "bonus_pink": (215, 8, 205, 180),
        "bonus_pink_alpha": (215, 8, 205, 80),
        "bonus_yellow": (214, 216, 8, 180),
        "bonus_yellow_alpha": (214, 216, 8, 80),
        "brown": (73, 60, 43, 255),
        "dark_orange": (164, 100, 34, 255),
        "dark_pink": (208, 60, 94, 255),
        "dark_purple": (68, 6, 110, 255),
        "dark_yellow": (180, 154, 4, 255),
        "ghost": (198, 198, 198, 120),
        "ghost_darker": (134, 134, 134, 120),
        "green": (68, 137, 26, 255),
        "light_blue": (49, 162, 242, 255),
        "light_green": (163, 206, 39, 255),
        "light_red": (219, 70, 104, 255),
        "orange": (235, 137, 49, 255),
        "pink": (224, 111, 139, 255),
        "purple": (136, 4, 118, 255),
        "red": (190, 38, 51, 255),
        "teal": (178, 220, 239, 255),
        "yellow": (247, 226, 107, 255),
    }

    Color = namedtuple("Color", ("main", "border"))
    colors = {
        "bonus_1": Color("bonus_yellow", "bonus_yellow_alpha"),
        "bonus_2": Color("bonus_green", "bonus_green_alpha"),
        "bonus_3": Color("bonus_orange", "bonus_orange_alpha"),
        "bonus_4": Color("bonus_blue", "bonus_blue_alpha"),
        "bonus_5": Color("bonus_pink", "bonus_pink_alpha"),
        "i": Color("blue", "light_blue"),
        "j": Color("pink", "dark_pink"),
        "l": Color("red", "light_red"),
        "o": Color("dark_orange", "orange"),
        "s": Color("green", "light_green"),
        "shadow": Color("ghost", "ghost_darker"),
        "t": Color("purple", "dark_purple"),
        "wall": Color("brown", "black"),
        "z": Color("yellow", "dark_yellow"),
    }

    @staticmethod
    def image_as_string(block, size):
        """Produces a block image as a RGBA string for pygame.image to load.

        Args::

            block: string block name, one of l, j, s, z, i, o, t, wall or ghost
            size: integer pixel height + width of the block

        Returns:
            RGBA as a string for the block with its colors and size
        """

        if block not in Blocks.colors.keys():
            raise TypeError("block {} is not a known block!".format(block))
        elif not hasattr(Blocks, "_image_cache"):
            setattr(Blocks, "_image_cache", {})
        if not hasattr(Blocks, "_image_cache_size"):
            setattr(Blocks, "_image_cache_size", size)

        if size != Blocks._image_cache_size:  # blocksize changed, regen
            Blocks._image_cache = {}
            Blocks._image_cache_size = size

        if block not in Blocks._image_cache:
            Blocks._image_cache[block] = Blocks._gen_image_string(block, size)

        return Blocks._image_cache[block]

    @staticmethod
    def _gen_image_string(block, size):
        """Generates the image string for the block to then cache."""

        # packs a single pixel as a string by color name
        pixel = lambda x : struct.pack("4B", *Blocks.rgba_codes[x])

        main_color = Blocks.colors[block].main
        border_color = Blocks.colors[block].border

        # rows which are fully border pixels
        full_border = [pixel(border_color)] * size

        if block == "wall":  # special pattern
            # rows which are not patterend...
            not_patterned = [pixel(border_color)]
            not_patterned.extend([pixel(main_color)] * (size - 2))
            not_patterned.append(pixel(border_color))

            # rows which are patterend (alternating main and border)
            patterend = [pixel(border_color)]
            _pattern_color = main_color
            _next_color = border_color
            for _ in range(1, size - 3, 2):
                patterend.extend([pixel(_pattern_color)] * 2)
                _pattern_color, _next_color = _next_color, _pattern_color
            while len(patterend) < size - 1:
                patterend.append(pixel(main_color))
            patterend.append(pixel(border_color))

            # build the entire block with the above definitions as rows
            block_pattern = list(full_border)
            _current_row = not_patterned
            _next_row = patterend
            for _ in range(1, size - 3, 2):
                block_pattern.extend(_current_row * 2)
                _current_row, _next_row = _next_row, _current_row
            while (len(block_pattern) / size) < size - 1:
                block_pattern.extend(not_patterned)
            block_pattern.extend(full_border)

        elif block.startswith("bonus_"):  # bonus block patterns
            level = int(block.split("_")[1])
            quarter = int(size / 4)

            block_pattern = []
            row_start = "main"
            next_row_start = "border"
            outer = Blocks.colors[block]

            if level > 1:
                inner = Blocks.colors["bonus_{}".format(level - 1)]
            else:
                inner = outer

            for row in range(size):
                current = row_start
                next_ = next_row_start
                row_start, next_row_start = next_row_start, row_start
                ab_row = []
                for column in range(size):
                    if quarter < row < quarter * 3:
                        if quarter < column < quarter * 3:
                            ab_row.append(pixel(getattr(inner, current)))
                        else:
                            ab_row.append(pixel(getattr(outer, current)))
                    else:
                        ab_row.append(pixel(getattr(outer, current)))
                    current, next_ = next_, current
                block_pattern.append("".join(ab_row))

        else:  # normal block pattern
            # determine dot size relative to block size at 1:8 ratio
            dot = int((1 / 8) * size)

            # not patterened rows, mostly main color with borders on the side
            not_patterned = [pixel(border_color)]
            not_patterned.extend([pixel(main_color)] * (size - 2))
            not_patterned.append(pixel(border_color))

            # patterned rows being rows with the dot in them
            patterned = [pixel(border_color)]
            patterned.extend([pixel(main_color)] * (size - 2 - (dot * 2)))
            patterned.extend([pixel(border_color)] * dot)
            patterned.extend([pixel(main_color)] * dot)
            patterned.append(pixel(border_color))

            # put together the block with the above row definitions
            block_pattern = list(full_border)
            block_pattern.extend(not_patterned * (size - 2 - (dot * 2)))
            block_pattern.extend(patterned * dot)
            block_pattern.extend(not_patterned * dot)
            block_pattern.extend(full_border)

        return b"".join(block_pattern)


class Block(pygame.sprite.Sprite):
    def __init__(self, location, block, bonus_points, game, *groups, **kwargs):
        super(Block, self).__init__(*groups)
        self.image = pygame.image.fromstring(
            Blocks.image_as_string(block, game.blocksize),
            (game.blocksize,) * 2,
            "RGBA",
        )
        self.rect = pygame.rect.Rect(location, (game.blocksize,) * 2)
        self.exploding = False
        self.bonus_points = bonus_points
        self.visible = kwargs.get("visible", True)
        self.name = block

    def update(self, dt, game):
        if self.exploding:
            # this sprite is dead
            self.explode(game)

    def explode(self, game):
        """Explodes this block."""

        # TODO: add animation
        self.kill()
        self.remove()
        if self.bonus_points:
            # this is a multiplier for the last score added
            game.score.game.multiply_last(self.bonus_points)
            my_location = (self.rect.x, self.rect.y)
            next_level = self.bonus_points - 1
            if next_level:
                game.spawn_bonus_block(my_location, next_level)
            else:
                game.bonus_blocks.remove(my_location)


if __name__ == "__main__":
    print(Blocks.image_as_string("bonus_4", 17))
