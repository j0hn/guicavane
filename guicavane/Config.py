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

try:
    import cPickle as pickle
except ImportError:
    import pickle

HOME_DIR = os.path.expanduser("~")
TEMP_DIR = tempfile.gettempdir()
CONFIG_DIR = os.path.join(HOME_DIR, ".guicavane")
IMAGES_DIR = os.path.join(CONFIG_DIR, "images")
CONFIG_FILE = os.path.join(CONFIG_DIR, "guicavane.conf")
MARKS_FILE = os.path.join(CONFIG_DIR, "marks.dat")

if sys.platform == "win32":
    VLC_LOCATION = os.path.join(os.environ["ProgramFiles"],
                                "VideoLAN", "VLC", "vlc.exe")
else:
    VLC_LOCATION = "/usr/bin/vlc"


DEFAULT_VALUES = {
    "player_location": VLC_LOCATION,
    "cache_dir": TEMP_DIR,
    "last_mode": "Shows",
    "favorites": [],
    "last_download_directory": HOME_DIR,
    "images_dir": IMAGES_DIR,
    "mega_user": "",
    "mega_pass": "",
    "cuevana_user": "",
    "cuevana_pass": "",
    "automatic_marks": True,
    "cached_percentage": 2,
    "player_arguments": "",
    "cached_percentage_on_movies": False,
    "filename_template": "<show> S<season>E<episode> - <name>"
}

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

class Marks(object):
    """
    Class that handles marks storege and access.
    """

    def __init__(self):
        """
        Initialization and creation of the file if necessary.
        """

        self.marks = []

        if not os.path.exists(MARKS_FILE):
            self.save()

        self.load()

    def load(self):
        """
        Loads the data from the file.
        """

        with open(MARKS_FILE) as filehandler:
            try:
                self.marks = pickle.load(filehandler)
            except:
                self.marks = []

    def save(self):
        """
        Saves the data to the file.
        """

        with open(MARKS_FILE, "w") as filehandler:
            pickle.dump(self.marks, filehandler)


    def add(self, name):
        """
        Adds a mark to the list.
        Saves the file right after adding.
        """

        if str(name) not in self.marks:
            self.marks.append(str(name))
            self.save()

    def remove(self, name):
        """
        Removes a mark from the list.
        Saves the file right after removing.
        """

        if str(name) in self.marks:
            self.marks.remove(str(name))
            self.save()

    def get_all(self):
        """
        Returns a list with all the marks.
        """

        return self.marks
