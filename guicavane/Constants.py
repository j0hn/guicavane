#!/usr/bin/env python
# coding: utf-8

"""
Guicavane constants.

Module with constants values.
"""

import os
import sys
import gtk
from Gettext import gettext

from Paths import GUI_DIR, IMAGES_DIR, SEP

# Modes
MODES = {
    "Shows": gettext("Shows"),
    "Movies": gettext("Movies"),
    "Favorites": gettext("Favorites"),
    "Latest": gettext("Latest movies"),
    "Recomended": gettext("Recomended movies"),
}

# Index of the columns on the tree views
FILE_VIEW_COLUMN_PIXBUF = 0
FILE_VIEW_COLUMN_TEXT = 1
FILE_VIEW_COLUMN_OBJECT = 2

NAME_LIST_COLUMN_TEXT = 0
NAME_LIST_COLUMN_OBJECT = 1

HOSTS_VIEW_COLUMN_PIXBUF = 0
HOSTS_VIEW_COLUMN_TEXT = 1
HOSTS_VIEW_COLUMN_OBJECT = 2

SITES_COLUMN_TEXT = 0
SITES_COLUMN_OBJECT = 1
SITES_COLUMN_IMAGE = 2

# Icons
IMAGE_FOLDER = gtk.Image()
IMAGE_FOLDER.set_from_file(IMAGES_DIR + SEP + "folder.png")
ICON_FOLDER = IMAGE_FOLDER.get_pixbuf()

IMAGE_FILE_MOVIE = gtk.Image()
IMAGE_FILE_MOVIE.set_from_file(IMAGES_DIR + SEP + "video_file.png")
ICON_FILE_MOVIE = IMAGE_FILE_MOVIE.get_pixbuf()

IMAGE_FILE_MOVIE_MARK = gtk.Image()
IMAGE_FILE_MOVIE_MARK.set_from_file(IMAGES_DIR + SEP + "video_file_mark.png")
ICON_FILE_MOVIE_MARK = IMAGE_FILE_MOVIE_MARK.get_pixbuf()

IMAGE_CASE_EMPTY = IMAGES_DIR + SEP + "case_empty.png"
IMAGE_CASE = IMAGES_DIR + SEP + "case.png"

# Url request timeout
DEFAULT_REQUEST_TIMEOUT = 15  # None for use python's default

# Custom DNS (for avoiding ISP blocking)
CUSTOM_DNS = {
    "www.cuevana.tv": "184.107.187.234",
}
