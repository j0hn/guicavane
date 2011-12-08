#!/usr/bin/env python
# coding: utf-8
# pylint: disable-msg=E1101

"""
Wizard. Helps user in the first run.
"""

# TODO: Add button to guess the player

import gtk
from guicavane.Config import Config
from guicavane.Paths import WIZARD_GUI_FILE


class Wizard(object):
    """ Wizard interface manager. """

    def __init__(self, parent):
        """ Creates the window and initializes the attributes. """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(WIZARD_GUI_FILE)
        self.builder.connect_signals(self)

        # Config
        self.config = Config.get()

        # Widgets
        glade_objects = ["wizard_window", "player_location_button"]

        for glade_object in glade_objects:
            setattr(self, glade_object, self.builder.get_object(glade_object))

        self.wizard_window.set_transient_for(parent)

    def show(self):
        """ Shows the window. """

        self.wizard_window.show_all()

    def hide(self):
        """ Hides the window. """

        self.wizard_window.hide()

    def _on_apply(self, _):
        """ Called when the user clicks on the apply button. """

        player_location = self.player_location_button.get_filename()

        if player_location != None:
            self.config.set_key("player_location", player_location)

        self.hide()
