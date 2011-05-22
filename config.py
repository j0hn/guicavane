#!/usr/bin/env python
# coding: utf-8

"""
Config.

A simple module to provide configuration files using json as format.
"""

import os
import json

DEFAULT_VALUES = {"player_command": "vlc %s",
                  "cache_dir": "/tmp"}


class Config:
    """
    Configuration manager.
    """

    def __init__(self, config_file):
        self.config_file = config_file

        self.data = {}

        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                f.write(json.dumps(DEFAULT_VALUES) + "\n")
                return

        with open(self.config_file) as f:
            data = f.read()
            if data:
                self.data = json.loads(data)

    def get_key(self, key):
        """
        Returns the value of the given key or the default
        value if it isn't set on the config or None
        if the key doesn't exists.
        """

        return self.data.get(key, self.get_default(key))

    def set_key(self, key, value):
        """
        Sets the value of the key and writes the config file.
        """

        self.data[key] = value

        with open(self.config_file, "w") as f:
            f.write(json.dumps(self.data) + "\n")

    def get_default(self, key):
        """
        Returns the default value of the given key.
        """

        return DEFAULT_VALUES.get(key, None)
