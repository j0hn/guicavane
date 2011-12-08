#!/usr/bin/env python
# coding: utf-8

import os
import sys
import tempfile

# Directory separator
SEP = os.sep

if sys.platform == "win32":
    MAIN_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    VLC_LOCATION = os.path.join(os.environ["ProgramFiles"], "VideoLAN", "VLC", "vlc.exe")
else:
    MAIN_DIR = os.path.dirname(__file__)
    VLC_LOCATION = "/usr/bin/vlc"

HOME_DIR = os.path.expanduser("~")

TEMP_DIR = tempfile.gettempdir()
CACHE_DIR = TEMP_DIR

CONFIG_DIR = os.path.join(HOME_DIR, ".guicavane")
CONFIG_FILE = os.path.join(CONFIG_DIR, "guicavane.conf")

COOKIES_FILE = os.path.join(CONFIG_DIR, "cookies.jar")

MARKS_FILE = os.path.join(CONFIG_DIR, "marks.slist")
FAVORITES_FILE = os.path.join(CONFIG_DIR, "favorites.slist")

IMAGES_DIR = os.path.join(MAIN_DIR, "Images")
COVER_IMAGES_DIR = os.path.join(CONFIG_DIR, "images")
HOSTS_IMAGES_DIR = os.path.join(IMAGES_DIR, "Downloaders")

GUI_DIR = os.path.join(MAIN_DIR, "Glade")

TRANSLATION_DIR = os.path.join(MAIN_DIR, "Translations")

# Gui Files
MAIN_GUI_FILE = GUI_DIR + SEP + "main.glade"
SETTINGS_GUI_FILE = GUI_DIR + SEP + "settings.glade"
HOSTS_GUI_FILE = GUI_DIR + SEP + "hosts.glade"
CAPTCHA_GUI_FILE = GUI_DIR + SEP + "captcha.glade"
WIZARD_GUI_FILE = GUI_DIR + SEP + "wizard.glade"
