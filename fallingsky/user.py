"""User data storage and retrieval."""


from __future__ import print_function

import io
import os
import sys
import json
import appdirs


_PATH = os.path.join(appdirs.user_data_dir(), "Falling Sky")
_EXT = "{}json".format(os.extsep)
_USER_PATH = lambda u : os.path.join(_PATH, "{}{}".format(u, _EXT))


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
        return [os.path.splitext(u)[0] for u in users if \
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
            "blocksize": 4,  # this is multiplied by 4 to ensure proper centres
            "fallrate": 1,
            "bonus_block_rate": 0,
            "show_shape_spawn_rate": False,
        }
        self.data = self._fetch()

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

        with open(self.file, "w") as openuser:
            json.dump(self.data, openuser)

    def __getitem__(self, item):
        """Access via self["item"] to self.data["item"]."""

        return self.data.__getitem__(item)

    def __setitem__(self, key, value):
        """Setitem's on the self.data key."""

        return self.data.__setitem__(key, value)

    def get(self, item, default=None):
        """Returns Dict.get on self.data."""

        return self.data.get(item, default)

    def update(self, other):
        """Dictionary update on self.data. THIS IS NOT THE SAVE METHOD!"""

        return self.data.update(other)
