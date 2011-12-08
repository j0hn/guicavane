#!/usr/bin/env python
# encoding: utf-8
# pylint: disable-msg=E1101

"""
Settings. Manages the gui of the settings.
"""

import gtk
import base64
from guicavane.Config import Config
from guicavane.Paths import SETTINGS_GUI_FILE

# Dict with host -> (username_input, password_input) to retrive the
# accounts information
HOSTS_INPUTS = {
    "megaupload": ("megaupload_username", "megaupload_password"),
}


class SettingsDialog(object):
    """ Settings interface manager. """

    def __init__(self, gui_manager):
        """ Creates the window and initializes the attributes. """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(SETTINGS_GUI_FILE)
        self.builder.connect_signals(self)

        self.gui_manager = gui_manager
        self.config = Config.get()

        # Widgets
        glade_objects = [
            "settings_dialog", "player_location_button",
            "player_arguments_entry", "megaupload_user_entry",
            "megaupload_pass_entry", "cache_dir_button", "automatic_marks",
            "use_custom_resolve", "filename_template", "automatic_start",
        ]

        for glade_object in glade_objects:
            setattr(self, glade_object, self.builder.get_object(glade_object))

    def show(self):
        """ Shows the window with the values correctly asigned. """

        # Get the config values
        player_location = self.config.get_key("player_location")
        player_arguments = self.config.get_key("player_arguments")
        cache_dir = self.config.get_key("cache_dir")
        automatic_marks = self.config.get_key("automatic_marks")
        use_custom_resolve = self.config.get_key("use_custom_resolve")
        filename_template = self.config.get_key("filename_template")
        automatic_start = self.config.get_key("automatic_start")

        # Set the values
        self.player_location_button.set_filename(player_location)
        self.player_arguments_entry.set_text(player_arguments)
        self.cache_dir_button.set_filename(cache_dir)
        self.automatic_marks.set_active(automatic_marks)
        self.use_custom_resolve.set_active(use_custom_resolve)
        self.filename_template.set_text(filename_template)
        self.automatic_start.set_active(automatic_start)

        # Accounts
        accounts = self.config.get_key("accounts")
        for host, data in accounts:
            if host in HOSTS_INPUTS:
                user_input = self.builder.get_object(HOSTS_INPUTS[host][0])
                passwd_input = self.builder.get_object(HOSTS_INPUTS[host][1])

                try:
                    user_input.set_text(data["username"])
                    passwd_input.set_text(base64.b64decode(data["password"]))
                except:
                    user_input.set_text("")
                    passwd_input.set_text("")

        # Show the dialog and hide on close
        self.settings_dialog.run()
        self.settings_dialog.hide()

    def _on_save_settings(self, *args):
        """ Saves the settings to the disk. """

        # Get the values
        player_location = self.player_location_button.get_filename()
        player_arguments = self.player_arguments_entry.get_text()
        cache_dir = self.cache_dir_button.get_filename()
        automatic_marks = self.automatic_marks.get_active()
        use_custom_resolve = self.use_custom_resolve.get_active()
        filename_template = self.filename_template.get_text()
        automatic_start = self.automatic_start.get_active()

        # Save the new values to the config
        if player_location != None:
            self.config.set_key("player_location", player_location)

        self.config.set_key("cache_dir", cache_dir)
        self.config.set_key("automatic_marks", automatic_marks)
        self.config.set_key("use_custom_resolve", use_custom_resolve)
        self.config.set_key("player_arguments", player_arguments)
        self.config.set_key("filename_template", filename_template)
        self.config.set_key("automatic_start", automatic_start)
        self.config.save()

        # Accounts:
        accounts = []
        for host in HOSTS_INPUTS:
            user = self.builder.get_object(HOSTS_INPUTS[host][0]).get_text()
            passwd = self.builder.get_object(HOSTS_INPUTS[host][1]).get_text()

            accounts.append((host, {"username": user,
                "password": base64.b64encode(passwd)}))

        self.config.set_key("accounts", accounts)

        # Relog
        self.gui_manager.login_accounts()

        # Hide the dialog
        self.settings_dialog.hide()
