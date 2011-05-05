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

# Constants
MODE_SHOWS = "Shows"
MODE_MOVIES = "Movies"


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

        # Creating a new filter model to allow the user filter the
        # shows and movies by typing on an entry box
        name_list = self.builder.get_object("nameList")
        name_model = name_list.get_model()
        self.name_filter = name_model.filter_new()
        self.name_filter.set_visible_func(self.visible_func)
        name_list.set_model(self.name_filter)

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

        mode = self.get_mode()

        if mode == MODE_SHOWS:
            self.set_mode_shows()
        else:
            self.set_mode_movies()

    def on_seasson_change(self, combo):
        """
        Called when the 'seasson' combobox changes value.
        This will only be fired if the 'mode' combobox is setted to 'Shows'.
        """

        # Precondition
        if self.get_mode() != MODE_SHOWS:
            return

        seasson = combobox_get_active_text(combo)
        show = self.get_selected_name()

        if not seasson:
            return

        file_viewer = self.builder.get_object("fileViewer")
        file_model = file_viewer.get_model()

        theme = gtk.icon_theme_get_default()
        file_icon = theme.load_icon(gtk.STOCK_FILE, 48, 0)

        seasson = "Temporada " + seasson  # Hopfully temporary fix
        for episode in self.pycavane.episodes_by_season(show, seasson):
            episode_name = "%.2d - %s" % (int(episode[1]), episode[2])
            file_model.append([file_icon, episode_name])

    def on_name_change(self, treeview):
        """
        Called when the user selects a movie or a show from the 'name list'.
        """

        selected_text = self.get_selected_name()

        if self.get_mode() == MODE_SHOWS:
            seassons_combo = self.builder.get_object("seassonCombo")
            seassons_model = seassons_combo.get_model()
            seassons_model.clear()

            seassons = self.pycavane.seasson_by_show(selected_text)
            for i in range(1, len(seassons)+1):
                # Here we're assuming that the server has the
                # seassons 1 to length(seassons) that could not be true. TODO
                seassons_model.append([i])

    def on_name_filter_change(self, entry):
        self.name_filter.refilter()

    def set_mode_shows(self):
        """
        Sets the current mode to shows.
        """

        # We show the seasson combobox
        seasson_combo = self.builder.get_object("seassonCombo")
        seasson_combo.set_sensitive(True)

        shows_model = self.builder.get_object("nameListstore")
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

        movies_model = self.builder.get_object("nameListstore")
        movies_model.clear()

        for letter in string.uppercase:
            movies_model.append([letter])

    def get_mode(self):
        """
        Returns the current mode.
        e.g the value of the mode combobox.
        The result will be the constant MODE_SHOWS or MODE_MOVIES.
        """

        mode_combobox = self.builder.get_object("modeCombo")
        mode_text = combobox_get_active_text(mode_combobox)

        # Poscondition
        assert mode_text == MODE_SHOWS or mode_text == MODE_MOVIES

        return mode_text

    def get_selected_name(self):
        """
        Returns the string of the selected item on the 'name list'.
        """

        treeview = self.builder.get_object("nameList")
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        selected_text = model.get_value(iter, 0)

        return selected_text

    def visible_func(self, model, iter):
        filter_entry = self.builder.get_object("nameFilter")
        filtered_text = filter_entry.get_text()

        row_text = model.get_value(iter, 0)

        if row_text:
            # Case insensitive search
            filtered_text = filtered_text.lower()
            row_text = row_text.lower()

            return filtered_text in row_text

        return False


def main():
    """
    Creates the window and starts gtk main loop.
    """

    guifile = "gui.glade"
    mainWindow = MainWindow(guifile)
    gtk.main()


if __name__ == "__main__":
    main()
