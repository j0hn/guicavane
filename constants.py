#!/usr/bin/env python
# coding: utf-8

"""
Guicavane constants.

Module with constants values.
"""

import gtk


# Modes
MODE_SHOWS = "Shows"
MODE_MOVIES = "Movies"
MODE_FAVORITES = "Favorites"
MODES = [MODE_SHOWS, MODE_MOVIES, MODE_FAVORITES]
# NOTE: MODES must be in the same order as they appear in the combobox

# Icons

GTK_DEFAULT_THEME = gtk.icon_theme_get_default()

IMAGE_FILE_MOVIE = gtk.Image()
IMAGE_FILE_MOVIE.set_from_file("images/video_file.png")
ICON_FILE_MOVIE = IMAGE_FILE_MOVIE.get_pixbuf()

ICON_FOLDER = GTK_DEFAULT_THEME.load_icon(gtk.STOCK_DIRECTORY, 48, 0)
