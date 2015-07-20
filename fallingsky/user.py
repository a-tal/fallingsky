"""User data storage and retrieval."""


from __future__ import print_function

import io
import os
import sys
import json
import appdirs


_PATH = os.path.join(appdirs.user_data_dir(), "Falling Sky")
_EXT = "{}json".format(os.extsep)
_USER_PATH = lambda u: os.path.join(_PATH, "{}{}".format(u, _EXT))


def get_users():
    """Returns a list of all known user names."""

    try:
        users = os.listdir(_PATH)
    except OSError as error:
        if error.errno == 2:  # _PATH doesn't exist, first time run
            os.makedirs(_PATH)
            return []
        else:
            raise
    else:
        return [os.path.splitext(u)[0] for u in users if
                os.path.splitext(u)[1] == _EXT]


def reset_users():
    """Use to clear all user scores."""

    for user in get_users():
        try:
            os.remove(_USER_PATH(user))
        except:
            pass


class UserData(object):
    """Saves and retrieves and is the user data.

    Initialize with the user's ID.

    usage example:

        user_data = UserData(user_id)
        play_level(user_data) # gameplay, updating user_data like a dict.. eg:
        user_data["levels_played"] += 1
        user_data.save()
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.file = _USER_PATH(self.user_id)
        self.defaults = {
            "user_id": self.user_id,
            "wins": 0,
            "losses": 0,
            "width": 10,
            "height": 25,
            "total_score": 0,
            "best_score": 0,
            "nexts": 4,
            "blocksize": 6,  # this is multiplied by 4 to ensure proper centres
            "fallrate": 1,
            "bonus_block_rate": 0,
            "spawn_rate": False,
        }
        self.data = self._sanity_check(self._fetch())

    def _sanity_check(self, config):
        """Ensure the values are sane and no extra keys are present."""

        limits = {
            "blocksize": lambda x: max(min(x // 2 * 2, 32), 1),
            "nexts": lambda x: max(min(x, 8), 0),
            "height": lambda x: max(min(x, 199), 10),
            "width": lambda x: max(min(x, 299), 6),
            "fallrate": lambda x: max(min(x, 21), 1),
            "bonus_block_rate": lambda x: max(min(x, 50), 0),
        }

        for key, func in limits.items():
            config[key] = func(config[key])

        keys_to_pop = []
        for key in config.keys():
            if key not in self.defaults:
                keys_to_pop.append(key)

        for key in keys_to_pop:
            config.pop(key)

        return config

    def _fetch(self):
        """Fetches the data from the user data store."""

        if os.path.isfile(self.file):
            try:
                with io.open(os.path.join(_PATH, self.file)) as openuser:
                    return json.load(openuser)
            except Exception as error:
                print("save file corruption. removing.")
                print(error, file=sys.stderr)
                os.remove(self.file)

        return self.defaults

    def save(self):
        """Saves the user data with the user data store."""

        self.data = self._sanity_check(self.data)
        with open(self.file, "w") as openuser:
            json.dump(self.data, openuser)

    def __getitem__(self, item):
        """Access via self["item"] to self.data["item"]."""

        return self.data.__getitem__(item)

    def __setitem__(self, key, value):
        """Setitem's on the self.data key."""

        return self.data.__setitem__(key, value)

    def __contains__(self, key):
        """Returns Dict.__contains__ on self.data."""

        return key in self.data

    def keys(self):
        return self.data.keys()

    def get(self, item, default=None):
        """Returns Dict.get on self.data."""

        return self.data.get(item, default)

    def pop(self, key, *args):
        """Returns Dict.pop on self.data."""

        return self.data.pop(key, *args)

    def update(self, other):
        """Dictionary update on self.data. THIS IS NOT THE SAVE METHOD!"""

        return self.data.update(other)

    def items(self):
        """Passthrough to self.data.items()."""

        return self.data.items()
