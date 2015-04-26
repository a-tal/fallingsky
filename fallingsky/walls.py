"""Generates invisible and visible walls."""


from __future__ import division


def arcade_mode(resolution=(960, 640), blocksize=16, width=20, height=70):
    """Builds regular boring, but scalable, rectangular walls.

    If given values that are too much to fit at the resolution and blocksize,
    it just fits as many as it can with some amount of space for next blocks,
    the hold block, stats...

    Args::

        resolution: (x, y) tuple of total screen width and height
        blocksize: pixel height per block
        width: integer number of blocks wide for the map
        height: integer number of blocks high for the map

    Returns::

        a tuple of a list of (x, y) coords of all walls (includes invisible),
        and a list of (x, y) coords of all visible walls for sprites/images
    """

    blocks_wide = int(resolution[0] / blocksize)
    blocks_high = int(resolution[1] / blocksize)

    mapwidth = str(blocks_wide)
    mapheight = str(blocks_high)
    tilewidth = tileheight = str(blocksize)

    centre_block = int(blocks_wide / 2)
    spread = int(width / 2)

    walls = []        # walls includes the invisible walls
    wall_blocks = []  # the coords to spawn wall blocks on
    for x_coord in range(centre_block - (spread + 1),
                         centre_block + (width - spread) + 1):
        # making walls the entire y-axis to prevent over the top/overhangs
        for y_coord in range(blocks_high):
            if (x_coord == centre_block - (spread + 1)) or \
                   (x_coord == centre_block + (width - spread)) or \
                   (y_coord == blocks_high - 2):
                # but only spawn wall block sprites where walls are :)
                coord = ((x_coord * blocksize), (y_coord * blocksize))
                if blocks_high - height < y_coord < blocks_high - 1:
                    wall_blocks.append(coord)
                walls.append(coord)

    return walls, wall_blocks


# TODO: more/different configurations
