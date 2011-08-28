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

        for downloader in result:
            icon = downloader.icon
            name = downloader.name
            self.hosts_icon_view_model.append([icon, name, downloader])

        self.hosts_window.show_all()

    def play_file(self, file_path):
        """ Starts the playing using downloader. """

        player_location = self.config.get_key("player_location")
        player_args = self.config.get_key("player_arguments").split()
        player_cmd = [player_location] + player_args + [file_path]

        self.player_process = subprocess.Popen(player_cmd)

        self.gui_manager.background_task(self.update, self.on_finish)

    def update(self):
        while self.player_process.poll() == None:
            print "reproduciendo"
            time.sleep(1)

    def on_finish(self, (is_error, result)):
        print "Done! bye bye"

    def download_subtitles(self, to_download, filepath, is_movie):
        """ Download the subtitle if it exists. """

        print "Obtain subtitle"

    def get_filename(self, to_download, is_movie):
        if is_movie:
            result = to_download[1]
        else:
            season_number = self.gui.current_seasson.split()[-1]
            show_name = self.gui.current_show
            name = to_download[2]
            episode_number = to_download[1]

            result = self.config.get_key("filename_template")
            result = result.replace("<show>", show_name)
            result = result.replace("<season>", "%.2d" % int(season_number))
            try:
                result = result.replace("<episode>", "%.2d" % int(episode_number))
            except:
                result = result.replace("<episode>", "%s" % str(episode_number))
            result = result.replace("<name>", name)

        result = result.replace(os.sep, "_")
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
        downloader = self.hosts_icon_view_model[path][HOSTS_VIEW_COLUMN_OBJECT]

        self.hosts_window.hide()
        downloader.process_url(self.play_file)
