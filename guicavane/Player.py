#!/usr/bin/env python
# encoding: utf-8

"""
Player. Handles the download and starts the player.
"""

import os
import gtk
import time
import gobject
import subprocess

import Downloaders
from Constants import HOSTS_GUI_FILE, HOSTS_VIEW_COLUMN_OBJECT


class Player(object):
    """
    Class that takes care of the downloading and correctly
    playing the file.
    """

    def __init__(self, gui_manager, file_object):
        self.gui_manager = gui_manager
        self.config = self.gui_manager.config
        self.file_object = file_object
        self.file_path = self.get_file_path()

        # Builder for the hosts selection
        self.hosts_builder = gtk.Builder()
        self.hosts_builder.add_from_file(HOSTS_GUI_FILE)
        self.hosts_builder.connect_signals(self)

        glade_objects = ["hosts_window", "hosts_icon_view",
                         "hosts_icon_view_model"]

        for glade_object in glade_objects:
            setattr(self, glade_object, self.hosts_builder.get_object(glade_object))

        self.gui_manager.background_task(self.get_hosts, self.display_hosts,
            status_message="Fetching hosts...", unfreeze=False)

    def get_hosts(self):
        """ Returns a list with the avaliable downloaders for the file. """

        result = []
        avaliable_downloaders = Downloaders.get_avaliable()

        hosts = self.file_object.file_hosts

        for host in hosts:
            if host in avaliable_downloaders:
                result.append(Downloaders.get(host, self.gui_manager, hosts[host]))

        return result

    def display_hosts(self, (is_error, result)):
        """ Shows up the hosts selecting window. """

        if is_error:
            self.gui_manager.report_error("Error displaying hosts: %s" % result)
            return

        gobject.idle_add(self.gui_manager.set_status_message, "")

        for downloader in result:
            icon = downloader.icon
            name = downloader.name
            self.hosts_icon_view_model.append([icon, name, downloader])

        self.hosts_window.show_all()

    def play(self):
        """ Starts the playing of the file on file_path. """

        self.gui_manager.background_task(self.fill_cache,
                        self.open_player, unfreeze=False)

    def fill_cache(self):
        """ Downloads some content to start safely the player. """

        # Wait for the file to exists
        while not os.path.exists(self.file_path):
            time.sleep(1)

        if self.downloader.file_size != None:
            # Waits %1 of the total download
            percent = self.downloader.file_size * 0.01

            while self.downloader.downloaded_size < percent:
                time.sleep(1)
        else:
            # Waits 2MB, just an arbitrary amount
            while self.downloader.downloaded_size < 2 * 1024 * 1024:
                time.sleep(1)

    def open_player(self, *args):
        """ Fires up a new process with the player runing. """

        gobject.idle_add(self.gui_manager.set_status_message,
                         "Playing: %s" % self.file_object.name)

        player_location = self.config.get_key("player_location")
        player_args = self.config.get_key("player_arguments").split()
        player_cmd = [player_location] + player_args + [self.file_path]

        self.player_process = subprocess.Popen(player_cmd)
        self.gui_manager.background_task(self.update,
                        self.on_finish, unfreeze=False)

    def update(self):
        """ Updates the GUI with downloading data. """

        file_size = self.downloader.file_size

        while self.player_process.poll() == None:
            downloaded_size = self.downloader.downloaded_size

            print "%%%.2f Downloaded" % ((downloaded_size / file_size) * 100)
            time.sleep(1)

    def on_finish(self, (is_error, result)):
        self.downloader.stop_downloading = True

    def download_subtitles(self, to_download, filepath, is_movie):
        """ Download the subtitle if it exists. """

        print "Obtain subtitle"

    def get_file_path(self):
        """ Returns the file path of the file. """

        # TODO: Implement
        #result = self.config.get_key("filename_template")
        #result = result.replace("<show>", show_name)
        #result = result.replace("<season>", "%.2d" % int(season_number))
        #result = result.replace("<episode>", "%s" % str(episode_number))
        #result = result.replace("<name>", self.file_object.name)
        #result = result.replace(os.sep, "_")

        result = "/tmp/" + self.file_object.name
        return result

    # ================================
    # =         CALLBACKS            =
    # ================================

    def _on_hosts_cancel(self, button):
        """ Called when the user press the cancel button on the
        hosts window. """

        self.hosts_window.hide()
        self.gui_manager.unfreeze()

    def _on_host_select(self, *args):
        """ Called whe the user presses the ok button or double
        clicks on the host. """

        cursor = self.hosts_icon_view.get_cursor()
        if cursor == None:
            return

        path = cursor[0]
        self.downloader = self.hosts_icon_view_model[path][HOSTS_VIEW_COLUMN_OBJECT]

        self.hosts_window.hide()
        self.downloader.process_url(self.play, self.file_path)
