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
CONFIG_DIR = HOME_DIR + os.sep + ".config" + os.sep + "guicavane"
IMAGES_DIR = CONFIG_DIR + os.sep + "images"
CONFIG_FILE = CONFIG_DIR + os.sep + "guicavane.conf"

if sys.platform == "win32":
    VLC_COMMAND = '"' + os.path.join(os.environ["ProgramFiles"],
                                     "VideoLAN", "VLC", "vlc.exe") + "'"
else:
    VLC_COMMAND = "vlc"

DEFAULT_VALUES = {"player_command": VLC_COMMAND + " %s",
                  "cache_dir": TEMP_DIR,
                  "last_mode": "Shows",
                  "favorites": [],
                  "last_download_directory": HOME_DIR,
                  "marks": [],
                  "images_dir": IMAGES_DIR}

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

        if not os.path.exists(self.config_file):
            self.data = DEFAULT_VALUES
            self.save()
            return

        with open(self.config_file) as filehandler:
            data = filehandler.read()
            if data == [] or data:
                try:
                    self.data = json.loads(data)
                except ValueError:
                    self.data = DEFAULT_VALUES

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

        for key in self.data:
            if not self.data[key]:
                self.data[key] = get_default(key)

        with open(self.config_file, "w") as filehandler:
            filehandler.write(json.dumps(self.data,
                                         sort_keys=True, indent=4) + "\n")
