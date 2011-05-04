#!/usr/bin/evn python
# coding: utf-8

"""
guicavana: graphical user interface for the website cuevana.tv

Uses gtk toolkit to provide the graphical interface of the website
Author: Gonzalo Garcia (A.K.A j0hn) <j0hn.com.ar@gmail.com>
"""

import os
import gtk
import string

import pycavane
from utils import combobox_get_active_text


class MainWindow:

    def __init__(self, guifile):
        """
        Creates the main window based on the glade file `guifile`.
        """

        # Precondition: must have guifile
        assert os.path.exists(guifile)

        self.builder = gtk.Builder()
        self.builder.add_from_file(guifile)

        self.pycavane = pycavane.Pycavane()

        window = self.builder.get_object("mainWindow")
        window.show_all()

        # We leave the magic connection to glade
        self.builder.connect_signals(self)

        # The default mode it's shows
        self.set_mode_shows()

    def on_destroy(self, widget):
        """
        Called when the window closes.
        """

        # We kill gtk
        gtk.main_quit()

    def on_mode_change(self, combo):
        """
        Called when the 'mode' combobox changes value.
        """

        mode = combobox_get_active_text(combo)

        if mode == "Shows":
            self.set_mode_shows()
        else:
            self.set_mode_movies()

    def on_seasson_change(self, combo):
        """
        Called when the 'seasson' combobox changes value.
        This will only be fired if the 'mode' combobox is setted to 'Shows'.
        """

        # Precondition
        mode_combobox = self.builder.get_object("modeCombo")
        mode_text = combobox_get_active_text(mode_combobox)
        assert mode_text == "Shows"

        print combobox_get_active_text(combo)

    def set_mode_shows(self):
        """
        Sets the current mode to shows.
        """

        # We show the seasson combobox
        seasson_combo = self.builder.get_object("seassonCombo")
        seasson_combo.set_sensitive(True)

        shows_list = self.builder.get_object("nameList")
        shows_model = shows_list.get_model()
        shows_model.clear()

        shows = self.pycavane.get_shows()
        for show in shows:
            shows_model.append([show[1]])

    def set_mode_movies(self):
        """
        Sets the current mode to movies.
        """

        # We won't be needing the seasson combobox so we hide it
        seasson_combo = self.builder.get_object("seassonCombo")
        seasson_combo.set_sensitive(False)

        movies_list = self.builder.get_object("nameList")
        movies_model = movies_list.get_model()
        movies_model.clear()

        for letter in string.uppercase:
            movies_model.append([letter])


def main():
    """
    Creates the window and starts gtk main loop.
    """

    guifile = "gui.glade"
    mainWindow = MainWindow(guifile)
    gtk.main()


if __name__ == "__main__":
    main()
