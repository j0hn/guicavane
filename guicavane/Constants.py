#!/usr/bin/env python
# coding: utf-8

"""
Guicavane constants.

Module with constants values.
"""

import os
import sys
import gtk

from Paths import GUI_DIR, IMAGES_DIR, SEP

# Gui Files
MAIN_GUI_FILE = GUI_DIR + SEP + "main.glade"
SETTINGS_GUI_FILE = GUI_DIR + SEP + "settings.glade"
HOSTS_GUI_FILE = GUI_DIR + SEP + "hosts.glade"

# Modes
MODE_SHOWS = "Shows"
MODE_MOVIES = "Movies"
MODE_FAVORITES = "Favorites"
MODES = [MODE_SHOWS, MODE_MOVIES, MODE_FAVORITES]
# NOTE: MODES must be in the same order as they appear in the combobox

# Index of the columns on the tree views
FILE_VIEW_COLUMN_PIXBUF = 0
FILE_VIEW_COLUMN_TEXT = 1
FILE_VIEW_COLUMN_OBJECT = 2

NAME_LIST_COLUMN_TEXT = 0
NAME_LIST_COLUMN_OBJECT = 1


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
