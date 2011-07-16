#!/usr/bin/env python
# coding: utf-8

"""
Config.

A simple module to provide configuration files using json as format.
"""

import os
import sys
import json
import tempfile

HOME_DIR = os.path.expanduser("~")
TEMP_DIR = tempfile.gettempdir()
CONFIG_DIR = os.path.join(HOME_DIR, ".config", "guicavane")
IMAGES_DIR = os.path.join(CONFIG_DIR, "images")
CONFIG_FILE = os.path.join(CONFIG_DIR, "guicavane.conf")

if sys.platform == "win32":
    VLC_LOCATION = os.path.join(os.environ["ProgramFiles"],
                                "VideoLAN", "VLC", "vlc.exe")
else:
    VLC_LOCATION = "/usr/bin/vlc"

DEFAULT_VALUES = {"player_location": VLC_LOCATION,
                  "cache_dir": TEMP_DIR,
                  "last_mode": "Shows",
                  "favorites": [],
                  "last_download_directory": HOME_DIR,
                  "marks": [],
                  "images_dir": IMAGES_DIR,
                  "automatic_marks": False,
                  "cached_percentage": 3,
                  "player_arguments": "",
                  "cached_percentage_on_movies": False}

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)


def get_default(key):
    """
    Returns the default value of the given key.
    """

    return DEFAULT_VALUES.get(key, None)


class Config:
    """
    Configuration manager. Uses json as config format.
    """

    def __init__(self):
        self.config_file = CONFIG_FILE

        self.data = {}

        if os.path.exists(self.config_file):
            with open(self.config_file) as filehandler:
                data = filehandler.read()

                try:
                    self.data = json.loads(data)
                except ValueError:
                    self.data = DEFAULT_VALUES
        else:
            self.data = DEFAULT_VALUES

        self.save()

    def get_key(self, key):
        """
        Returns the value of the given key or the default
        value if it isn't set on the config or None
        if the key doesn't exists.
        """

        return self.data.get(key, get_default(key))

    def set_key(self, key, value):
        """
        Sets the value of the key and writes the config file.
        """

        self.data[key] = value

    def append_key(self, key, value):
        """
        If the key is a list, appends the value to the list.
        """

        if not key in self.data:
            self.data[key] = get_default(key)

        assert type(self.data[key]) == list

        self.data[key].append(value)

    def remove_key(self, key, value):
        """
        If the key is a list, removes the value from it.
        """

        assert type(self.data[key]) == list
        assert value in self.data[key]

        self.data[key].remove(value)

    def save(self):
        """
        Saves the config on the disk file and fills
        the empty values with default ones.
        """

        for key in DEFAULT_VALUES:
            if key not in self.data:
                self.data[key] = get_default(key)

        with open(self.config_file, "w") as filehandler:
            json_data = json.dumps(self.data, sort_keys=True, indent=4)
            filehandler.write(json_data + "\n")
