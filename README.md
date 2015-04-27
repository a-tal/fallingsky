The Tragedy of the Falling Sky
==============================

[View on GitHub pages](http://a-tal.github.io/fallingsky/)

[![Version](https://img.shields.io/pypi/v/fallingsky.svg)](https://pypi.python.org/pypi/fallingsky/)
[![Build Status](https://img.shields.io/travis/a-tal/fallingsky.svg)](https://travis-ci.org/a-tal/fallingsky)
[![Download format](https://img.shields.io/badge/format-wheel-green.svg?)](https://pypi.python.org/pypi/fallingsky/)
[![Test Coverage](https://img.shields.io/coveralls/a-tal/fallingsky.svg)](https://coveralls.io/r/a-tal/fallingsky)
[![Downloads this month](https://img.shields.io/pypi/dm/fallingsky.svg)](https://pypi.python.org/pypi/fallingsky/)
[![Supported Python versions](https://img.shields.io/badge/python-2.7,%203.4-blue.svg)](https://pypi.python.org/pypi/fallingsky/)
[![Supported Python implementations](https://img.shields.io/badge/implementation-cpython-blue.svg)](https://pypi.python.org/pypi/fallingsky/)
[![Development Status](https://img.shields.io/badge/status-pre--alpha-red.svg)](https://pypi.python.org/pypi/fallingsky/)
[![License](https://img.shields.io/pypi/l/fallingsky.svg)](https://pypi.python.org/pypi/fallingsky/)

A game of falling blocks with RPG elements, uses pygame. In very early development, feel free to help out!

![](https://raw.githubusercontent.com/a-tal/fallingsky/gh-pages/images/demo.gif)


Installation
============

Pygame
------

If you don't have pygame installed yet, you'll need that.

On MacOS, you can do the following:

```bash
$ brew install python  # missing brew? go here http://brew.sh/
$ brew install sdl sdl_image sdl_mixer sdl_ttf smpeg portmidi
$ # create and/or activate a virtualenv here (optional)
$ yes | pip install hg+http://bitbucket.org/pygame/pygame
```

On Ubuntu (tested on 15.04 desktop),

```bash
$ sudo apt-get install python-pip mercurial
$ sudo apt-get build-dep pygame
$ # create and/or activate a virtualenv here (optional)
$ yes | pip install hg+http://bitbucket.org/pygame/pygame
```

On Windows, install the pygame binaries from [pygame.org](http://pygame.org/download.shtml).


Fallingsky
----------

With pygame installed, you can now clone this repo or install it like a normal python package:

```bash
$ pip install fallingsky
```

If you want to grab the source to hack on it as well:

```bash
$ git clone https://github.com/a-tal/fallingsky.git
$ cd fallingsky
$ python setup.py develop
```

Either way, you should now have a `fallingsky` executable in your `$PATH`.


Configuration
=============

Everything in The Tragedy of the Falling Sky is meant to be dynamic. This includes:

* the screen resolution
* the block size
* maximum game board width & height
* block drop/turn/move/hold/slam delays

Currently planning on adding game play elements to do with unlocking the ability to adjust these in game. If you want, you can hack around it by changing your user preferences or launching the game through the hack back door (see [main.py](https://github.com/a-tal/fallingsky/raw/master/fallingsky/main.py)).

Your user preferences are stored in a platform specific/standard place. On Linux that is `~/.config/fallingsky`, on Mac it'd be `~/Library/Application Support/fallingsky` and on Windows, if this works, it'd save to `%HOMEDRIVE%\\%HOMEPATH%\\AppData\\Local\\fallingsky`. Inside that folder is a list of JSON files for each user.


TODOs
=====

Obviously the "artwork" is a little rough around the edges. But that's not a super high concern right now, although if someone was to offer up a better color palette that could easily be implemented and would be appreciated.

Need to make a better UI for between games. Something to track progress better, maybe track each score as well instead of just total and best to show progress over time.

Different maps. Shapes other than a rectangle. An interface for the user to select what height+width they want to use if doing arcade mode.

Sound effects. Background music.

Better backgrounds everywhere. Some pattern for arcade mode that painted the game board a bit better as well as the hold area and next area.

An interface to select how many next blocks you want. Next blocks in rows as well as columns. Some mechanism for earning more next blocks.

Better scoring. An interface to show how the difficulty of options you've selected has impacted the score modifier. Better display of points as the user scores them.

Explosion animations.

Configurable controls.

UI to configure the resolution and the block size.

Network capabilities, PvP gameplay elements, AI for PvE.


Copyright and License
=====================

The Tragedy of the Falling Sky<br />
Copyright (C) 2015 Adam Talsma.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; version 2.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to:

    Free Software Foundation, Inc.
    51 Franklin Street, Fifth Floor
    Boston, MA, USA 02110-1301
