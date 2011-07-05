#!/usr/bin/env python
# encoding: utf-8

"""
Settings. Manages the gui of the settings.
"""

import gtk
from constants import SETTINGS_GUI_FILE


class Settings(object):
    """
    Settings interface manager.
    """

    def __init__(self, config):
        """
        Creates the window and initializes the attributes.
        """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(SETTINGS_GUI_FILE)
        self.builder.connect_signals(self)

        # Config
        self.config = config

        # Widgets
        self.main_dialog = self.builder.get_object("settingsDialog")
        self.player_cmd_entry = self.builder.get_object("playerCommandEntry")
        self.cache_dir_button = self.builder.get_object("cachedirButton")
        self.automatic_marks_button = self.builder.get_object("automaticMarks")

    def show(self):
        """
        Shows the window with the values correctly asigned.
        """

        # Get the config values
        player_cmd = self.config.get_key("player_command")
        cache_dir = self.config.get_key("cache_dir")
        automatic_marks = self.config.get_key("automatic_marks")

        # Set the values
        self.player_cmd_entry.set_text(player_cmd)
        self.cache_dir_button.set_filename(cache_dir)
        self.automatic_marks_button.set_active(automatic_marks)

        # Show the dialog and hide on close
        self.main_dialog.run()
        self.main_dialog.hide()

    def _on_save_settings(self, *args):
        """
        Saves the settings to the disk.
        """

        # Get the values
        player_cmd = self.player_cmd_entry.get_text()
        cache_dir = self.cache_dir_button.get_filename()
        automatic_marks = self.automatic_marks_button.get_active()

        # Save the new values to the config
        self.config.set_key("player_command", player_cmd)
        self.config.set_key("cache_dir", cache_dir)
        self.config.set_key("automatic_marks", automatic_marks)
        self.config.save()

        # Hide the dialog
        self.main_dialog.hide()
