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
from megaupload import MegaFile
from login import MegaAccount
from Constants import HOSTS_GUI_FILE, HOSTS_VIEW_COLUMN_OBJECT


class Player(object):
    """
    Class that takes care of the downloading and correctly
    playing the file.
    """

    def __init__(self, gui_manager, file_object):
        self.gui_manager = gui_manager
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

        #self.account = MegaAccount()

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
            print "ERROR: %s" % result
            return

        for downloader in result:
            icon = downloader.icon
            name = downloader.name
            self.hosts_icon_view_model.append([icon, name, downloader])

        self.hosts_window.show_all()

    def play_file(self, file_path):
        """ Starts the playing using downloader. """

        #self.download_subtitles()
        print "play here!!"
        self.gui_manager.unfreeze()
        return

        if file_path:
            cache_dir = file_path
        else:
            cache_dir = self.config.get_key("cache_dir")

        if is_movie:
            title = to_download[1]
        else:
            title = to_download[2]

        # Check login status
        if not self.account.verified:
            username = self.config.get_key("mega_user")
            password = self.config.get_key("mega_pass")

            if password:
                self.account.login(username, password)

        # Create the megaupload instance
        filename = self.get_filename(to_download, is_movie)
        megafile = MegaFile(link, cache_dir, self.account,
                            self.on_megaupload_error, filename)
        filepath = megafile.cache_file

        # Download the subtitles
        self.download_subtitles(to_download, filepath, is_movie)

        # Start the file download
        megafile.start()

        # Waiting megaupload link
        for i in xrange(self.account.wait, 1, -1):
            loading_dots = "." * (3 - i % 4)
            self.set_status_message("Please wait %d seconds%s" % \
                                (i, loading_dots))
            time.sleep(1)

        # Wait until the file exists
        file_exists = False
        while not file_exists:
            if self.megaupload_error:
                raise Exception("Download error: time exceeded")
            else:
                self.set_status_message("A few seconds left...")
                file_exists = os.path.exists(filepath)
                time.sleep(1)

        if download_only:
            self.set_status_message("Downloading: %s" % title)
        else:
            self.set_status_message("Now playing: %s" % title)

        # Show the progress bar
        gobject.idle_add(self.show_progress)

        cache_on_movies = self.config.get_key("cached_percentage_on_movies")
        cached_percentage = self.config.get_key("cached_percentage")
        cached_percentage = cached_percentage / 100.0

        if is_movie and not cache_on_movies:
            cached_percentage = 0.008

        player_location = self.config.get_key("player_location")
        player_args = self.config.get_key("player_arguments").split()

        size = megafile.size * 1024.0  # In KB
        stop = False
        running = False
        speed_list = []
        last_downloaded = 0
        while not stop:
            time.sleep(1)

            downloaded = megafile.downloaded_size * 1024.0  # In KB
            speed_list.append(downloaded - last_downloaded)
            offset = len(speed_list) - 30 if len(speed_list) > 30 else 0
            speed_list = speed_list[offset:]

            speed_avarage = sum(speed_list) / len(speed_list)
            last_downloaded = downloaded

            fraction = downloaded / size

            if download_only:
                if round(fraction, 2) >= 1:
                    stop = True
            else:
                if not running and fraction > cached_percentage:
                    player_cmd = [player_location] + player_args + [filepath]
                    process = subprocess.Popen(player_cmd)
                    running = True

                if running and process.poll() != None:
                    stop = True

            if speed_avarage <= 0:
                remaining_time = 0
            else:
                remaining_time = ((size - downloaded) / speed_avarage) / 60

            if remaining_time >= 1:  # if it's more than a minute
                if remaining_time == 1:
                    remaining_message = "%d minute left" % remaining_time
                else:
                    remaining_message = "%d minutes left" % remaining_time
            else:
                if (remaining_time * 60) > 10:
                    remaining_message = "%d seconds left" % (remaining_time * 60)
                elif remaining_time != 0:
                    remaining_message = "a few seconds left"
                else:
                    remaining_message = ""

            if fraction < 1:
                gobject.idle_add(self.gui.progress_label.set_text,
                    "%.2fKB/s - %s" % (speed_avarage, remaining_message))
            else:
                gobject.idle_add(self.gui.progress_label.set_text, "")

            gobject.idle_add(self.gui.progress.set_fraction, fraction)
            gobject.idle_add(self.gui.progress.set_text,
                             "%.2f%%" % (fraction * 100))

        gobject.idle_add(self.gui.progress_box.hide)

        # Automatic mark
        if self.config.get_key("automatic_marks"):
            self.gui.mark_selected()

        megafile.released = True

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

    def show_progress(self):
        self.gui.progress_box.show()
        self.gui.progress.set_fraction(0.0)

    def on_megaupload_error(self, error):
        self.megaupload_error = True

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
