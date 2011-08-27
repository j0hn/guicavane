#!/usr/bin/env python
# coding: utf-8

import os
import sys
import tempfile

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
