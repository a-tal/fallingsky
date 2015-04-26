"""Utility functions used in The Tragedy of the Falling Sky."""


import os
import pygame


def _here():
    """Returns the current full directory path."""

    return os.path.dirname(os.path.realpath(__file__))


def load_image(image_name):
    """Loads the image_name from the "images" directory.

    Args:
        image_name: string image file name, with extension

    Returns:
        the result of pygame.image.load for the image file
    """

    return pygame.image.load(os.path.join(_here(), "images", image_name))


def load_sound(sound_file):
    """Loads the sound_file from the "sounds" directory.

    Args:
        sound_file: string name of the sound file with extension

    Returns:
        instantiated pygame.mixer.Sound object for the sound file
    """

    return pygame.mixer.Sound(os.path.join(_here(), "sounds", sound_file))
