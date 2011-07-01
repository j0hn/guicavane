#!/usr/bin/env python
# coding: utf-8

"""
Guicavane constants.

Module with constants values.
"""

import os
import sys
import gtk

# Directory separator
SEP = os.sep

# Allow correctly opening from outside
MAIN_DIR = os.path.dirname(__file__)
GUI_FILE = MAIN_DIR + SEP + "gui" + SEP + "main.glade"

# Modes
MODE_SHOWS = "Shows"
MODE_MOVIES = "Movies"
MODE_FAVORITES = "Favorites"
MODES = [MODE_SHOWS, MODE_MOVIES, MODE_FAVORITES]
# NOTE: MODES must be in the same order as they appear in the combobox

# Index of the columns on the tree views
FILE_VIEW_COLUMN_PIXBUF = 0
FILE_VIEW_COLUMN_TEXT = 1
NAME_COLUMN_TEXT = 0

# Icons
IMAGE_FOLDER = gtk.Image()
IMAGE_FOLDER.set_from_file("images/folder.png")
ICON_FOLDER = IMAGE_FOLDER.get_pixbuf()

IMAGE_FILE_MOVIE = gtk.Image()
IMAGE_FILE_MOVIE.set_from_file("images/video_file.png")
ICON_FILE_MOVIE = IMAGE_FILE_MOVIE.get_pixbuf()

IMAGE_FILE_MOVIE_MARK = gtk.Image()
IMAGE_FILE_MOVIE_MARK.set_from_file("images/video_file_mark.png")
ICON_FILE_MOVIE_MARK = IMAGE_FILE_MOVIE_MARK.get_pixbuf()
