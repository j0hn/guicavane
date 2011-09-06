#!/usr/bin/env python
# coding: utf-8

import os
import sys
import tempfile

# Directory separator
SEP = os.sep

MAIN_DIR = os.path.dirname(__file__)
HOME_DIR = os.path.expanduser("~")

TEMP_DIR = tempfile.gettempdir()

CONFIG_DIR = os.path.join(HOME_DIR, ".guicavane")
CONFIG_FILE = os.path.join(CONFIG_DIR, "guicavane.conf")

MARKS_FILE = os.path.join(CONFIG_DIR, "marks.dat")

IMAGES_DIR = os.path.join(MAIN_DIR, "images")
HOSTS_IMAGES_DIR = os.path.join(IMAGES_DIR, "hosts")

GUI_DIR = os.path.join(MAIN_DIR, "glade")

if sys.platform == "win32":
    VLC_LOCATION = os.path.join(os.environ["ProgramFiles"], "VideoLAN", "VLC", "vlc.exe")
else:
    VLC_LOCATION = "/usr/bin/vlc"
