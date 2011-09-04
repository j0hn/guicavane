#!/usr/bin/env python
# encoding: utf-8

"""
Settings. Manages the gui of the settings.
"""

import gtk
from Constants import SETTINGS_GUI_FILE

HOSTS = {"megaupload": ("mega_user", "mega_pass"),
        }


class SettingsDialog(object):
    """ Settings interface manager. """

    def __init__(self, config, accounts):
        """ Creates the window and initializes the attributes. """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(SETTINGS_GUI_FILE)
        self.builder.connect_signals(self)

        # Config and Accounts
        self.config = config
        self.accounts = accounts

        # Widgets
        glade_objects = [
            "settings_dialog", "player_location_button", "player_arguments_entry",
            "megaupload_user_entry", "megaupload_pass_entry", "cuevana_user_entry",
            "cuevana_pass_entry", "cache_dir_button", "automatic_marks",
            "filename_template",
        ]

        for glade_object in glade_objects:
            setattr(self, glade_object, self.builder.get_object(glade_object))

        # First login
        self._update_accounts()

    def show(self):
        """ Shows the window with the values correctly asigned. """

        # Get the config values
        player_location = self.config.get_key("player_location")
        player_arguments = self.config.get_key("player_arguments")
        mega_user = self.config.get_key("mega_user")
        mega_pass = self.config.get_key("mega_pass")
        cuevana_user = self.config.get_key("cuevana_user")
        cuevana_pass = self.config.get_key("cuevana_pass")
        cache_dir = self.config.get_key("cache_dir")
        automatic_marks = self.config.get_key("automatic_marks")
        filename_template = self.config.get_key("filename_template")

        # Set the values
        self.player_location_button.set_filename(player_location)
        self.player_arguments_entry.set_text(player_arguments)
        self.megaupload_user_entry.set_text(mega_user)
        self.megaupload_pass_entry.set_text(mega_pass)
        self.cuevana_user_entry.set_text(cuevana_user)
        self.cuevana_pass_entry.set_text(cuevana_pass)
        self.cache_dir_button.set_filename(cache_dir)
        self.automatic_marks.set_active(automatic_marks)
        self.filename_template.set_text(filename_template)

        # Show the dialog and hide on close
        self.settings_dialog.run()
        self.settings_dialog.hide()

    def _on_save_settings(self, *args):
        """ Saves the settings to the disk. """

        # Get the values
        player_location = self.player_location_button.get_filename()
        player_arguments = self.player_arguments_entry.get_text()
        mega_user = self.megaupload_user_entry.get_text()
        mega_pass = self.megaupload_pass_entry.get_text()
        cuevana_user = self.cuevana_user_entry.get_text()
        cuevana_pass = self.cuevana_pass_entry.get_text()
        cache_dir = self.cache_dir_button.get_filename()
        automatic_marks = self.automatic_marks.get_active()
        filename_template = self.filename_template.get_text()

        # Save the new values to the config
        self.config.set_key("player_location", player_location)
        self.config.set_key("mega_user", mega_user)
        self.config.set_key("mega_pass", mega_pass)
        self.config.set_key("cuevana_user", cuevana_user)
        self.config.set_key("cuevana_pass", cuevana_pass)
        self.config.set_key("cache_dir", cache_dir)
        self.config.set_key("automatic_marks", automatic_marks)
        self.config.set_key("player_arguments", player_arguments)
        self.config.set_key("filename_template", filename_template)
        self.config.save()

        # Relog
        self._update_accounts()

        # Hide the dialog
        self.settings_dialog.hide()

    def _update_accounts(self):
        """Logs into the accounts with the config settings."""

        for host in HOSTS:
            username = self.config.get_key(HOSTS[host][0])
            password = self.config.get_key(HOSTS[host][1])

            self.accounts[host].login(username, password)
