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
from guicavane.Config import Config
from guicavane.Gettext import gettext
from guicavane.Utils.Log import console
from guicavane.Utils.UrlOpen import UrlOpen
from guicavane.Paths import HOSTS_GUI_FILE
from guicavane.Hosts.Base import BaseMovie, BaseEpisode
from guicavane.Constants import HOSTS_VIEW_COLUMN_OBJECT, \
                                HOSTS_VIEW_COLUMN_TEXT

log = console("Player")


class Player(object):
    """
    Class that takes care of the downloading and correctly
    playing the file.
    """

    def __init__(self, gui_manager, file_object,
                 file_path=None, download_only=False, choose_host=False):
        self.gui_manager = gui_manager
        self.config = Config.get()

        self.file_object = file_object
        self.download_only = download_only
        self.choose_host = choose_host

        self.selected_quality = None

        self._speed_list = []
        self._last_downloaded_size = 0
        self.speed = 0

        self.file_path = file_path
        if not self.file_path:
            self.file_path = self.config.get_key("cache_dir")

        self.file_path = os.path.join(self.file_path, self.get_filename())

        # Builder for the hosts selection
        self.hosts_builder = gtk.Builder()
        self.hosts_builder.add_from_file(HOSTS_GUI_FILE)
        self.hosts_builder.connect_signals(self)

        glade_objects = ["hosts_window", "hosts_icon_view",
                         "hosts_icon_view_model"]

        for glade_object in glade_objects:
            setattr(self, glade_object,
                self.hosts_builder.get_object(glade_object))

        self.gui_manager.background_task(self.get_hosts, self.display_hosts,
            status_message=gettext("Fetching hosts..."), unfreeze=False)

    def get_hosts(self):
        """ Returns a dict with the avaliable downloaders for the file. """

        result = {}
        avaliable_downloaders = Downloaders.get_avaliable()

        hosts = self.file_object.file_hosts

        hosts["dummy"] = ""

        for host in hosts:
            host = host.lower()
            if host in avaliable_downloaders:
                result[host] = hosts[host]

        return result

    def display_hosts(self, (is_error, result)):
        """ Shows up the hosts selecting window. """

        if is_error:
            self.gui_manager.report_error(gettext("Error fetching hosts: %s") % \
                                          result)
            gobject.idle_add(self.gui_manager.progress.hide)
            return


        gobject.idle_add(self.gui_manager.set_status_message, "")

        if not result:
            self.gui_manager.report_error(gettext("No host found"))
            self.gui_manager.unfreeze()
            return

        automatic_start = self.config.get_key("automatic_start")

        if automatic_start and len(result) == 1 and not self.choose_host:
            host, qualities = result.items()[0]

            if len(qualities) == 1:
                gobject.idle_add(self.gui_manager.set_status_message,
                    gettext("Only one host found, starting download..."))

                url = qualities.items()[0][1]
                self.downloader = Downloaders.get(host, self.gui_manager, url)
                self.downloader.process_url(self.play, self.file_path)
                return

        # elif len(result) == 1 and not self.choose_host:
        #     gobject.idle_add(self.gui_manager.set_status_message,
        #         "Only one host found, starting download...")
        #     self.downloader = result[0]
        #     self.downloader.process_url(self.play, self.file_path)
        # else:
        #     megaupload = [x for x in result if x.name == "Megaupload"]
        #     if not self.choose_host and len(megaupload) != 0 and \
        #            self.config.get_key("automatic_megaupload"):

        #         gobject.idle_add(self.gui_manager.set_status_message,
        #             "Automatically starting with megaupload")
        #         self.downloader = megaupload[0]
        #         self.downloader.process_url(self.play, self.file_path)
        #     else:
        #         for downloader in result:
        #             icon = downloader.icon
        #             name = downloader.name
        #             self.hosts_icon_view_model.append([icon, name, downloader])

        #         self.hosts_window.show_all()

        for host in result:
            for quality in result[host]:
                downloader = Downloaders.get(host, self.gui_manager,
                                             result[host][quality])
                icon = downloader.icon
                name = "%s (%s)" % (downloader.name, quality)

                self.hosts_icon_view_model.append([icon, name, downloader])

        self.hosts_window.show_all()

    def play(self):
        """ Starts the playing of the file on file_path. """

        self.gui_manager.background_task(self.pre_download,
            self.open_player, unfreeze=False)

        self.gui_manager.background_task(self.download_subtitle,
            self._on_download_subtitle_finish, unfreeze=False)

    def pre_download(self):
        """ Downloads some content to start safely the player. """

        # Download the subtitle
        gobject.idle_add(self.gui_manager.set_status_message,
            gettext("Downloading subtitles..."))

        # Wait for the file to exists
        gobject.idle_add(self.gui_manager.set_status_message,
                         gettext("Please wait..."))
        while not os.path.exists(self.file_path):
            time.sleep(1)

        # Show the progress bar box
        gobject.idle_add(self.gui_manager.progress.set_fraction, 0.0)
        gobject.idle_add(self.gui_manager.progress_box.show)
        gobject.idle_add(self.gui_manager.set_status_message,
                         gettext("Filling cache..."))

        if self.downloader.file_size != 0:
            # Waits %1 of the total download
            percent = self.downloader.file_size * 0.01

            while self.downloader.downloaded_size < percent:
                self._update_progress()
                self.update_speed()
                time.sleep(1)
        else:
            # Waits 2MB, just an arbitrary amount
            while self.downloader.downloaded_size < 2 * 1024 * 1024:
                gobject.idle_add(self.gui_manager.progress.pulse)
                time.sleep(0.5)

    def open_player(self, (is_error, result)):
        """ Fires up a new process with the player runing. """

        if is_error:
            self.gui_manager.report_error(gettext("Error pre-downloading: %s") % result)
            return

        if self.download_only:
            message = gettext("Downloading: %s")
        else:
            message = gettext("Playing: %s")

        gobject.idle_add(self.gui_manager.set_status_message,
                         message % self.file_object.name)

        player_location = self.config.get_key("player_location")
        player_args = self.config.get_key("player_arguments").split()
        player_cmd = [player_location] + player_args + [self.file_path]

        if not self.download_only:
            self.player_process = subprocess.Popen(player_cmd)

        self.gui_manager.background_task(self.update, self.on_finish)

    def update_speed(self):
        downloaded_size = self.downloader.downloaded_size
        self._speed_list.append((downloaded_size - self._last_downloaded_size) / 1024.0)

        list_offset = len(self._speed_list) - 30 if len(self._speed_list) > 30 else 0
        self._speed_list = self._speed_list[list_offset:]
        self.speed = sum(self._speed_list) / len(self._speed_list)
        self._last_downloaded_size = downloaded_size

    def update(self):
        """ Updates the GUI with downloading data. """

        stop = False

        while not stop:
            downloaded_size = self.downloader.downloaded_size

            self.update_speed()

            if self.speed > 0:
                remaining_size = (self.downloader.file_size - downloaded_size) / 1024.0
                remaining_time = (remaining_size / self.speed) / 60
            else:
                remaining_time = 0

            if remaining_time >= 1:  # if it's more than a minute
                if remaining_time == 1:
                    remaining_message = gettext("%d minute left") % remaining_time
                else:
                    remaining_message = gettext("%d minutes left") % remaining_time
            else:
                if (remaining_time * 60) > 10:
                    remaining_message = gettext("%d seconds left") % (remaining_time * 60)
                elif remaining_time != 0:
                    remaining_message = gettext("a few seconds left")
                else:
                    remaining_message = ""

            if downloaded_size < self.downloader.file_size:
                gobject.idle_add(self.gui_manager.progress_label.set_text, \
                    "%.2fKB/s - %s" % (self.speed, remaining_message))
            else:
                gobject.idle_add(self.gui_manager.progress_label.set_text, "")

            if self.downloader.file_size != 0:
                self._update_progress()
                time.sleep(1)
            else:
                gobject.idle_add(self.gui_manager.progress.pulse)
                time.sleep(1)

            stop = downloaded_size == self.downloader.file_size

            if not self.download_only:
                stop |= self.player_process.poll() != None

    def _update_progress(self):
        """ Updates the progress bar using the downloaded size and the
        total file size if posible. """

        downloaded_size = self.downloader.downloaded_size
        file_size = self.downloader.file_size

        fraction = downloaded_size / file_size
        gobject.idle_add(self.gui_manager.progress.set_fraction, fraction)
        gobject.idle_add(self.gui_manager.progress.set_text,
            "%.2f%%" % (fraction * 100))

    def on_finish(self, (is_error, result)):
        assert not is_error, str(result)

        self.downloader.stop_downloading = True

        # Hide the progress
        gobject.idle_add(self.gui_manager.progress_box.hide)
        gobject.idle_add(self.gui_manager.set_status_message, "")

        downloaded_size = self.downloader.downloaded_size
        file_size = self.downloader.file_size

        if downloaded_size >= file_size:
            if self.config.get_key("automatic_marks"):
                if isinstance(self.file_object, BaseMovie):
                    mark_string = "%s" % self.file_object.name
                else:
                    mark_string = "%s-%s-%s" % (self.file_object.show.name,
                        self.file_object.season.name, self.file_object.name)

                log.info("Mark automatically added: %s" % mark_string)

                self.gui_manager.marks.add(mark_string)
                self.gui_manager.refresh_marks()

    def get_filename(self):
        """ Returns the file path of the file. """

        if isinstance(self.file_object, BaseMovie):
            return self.file_object.name.replace(os.sep, "_") + ".mp4"

        # If isn't a movie it must be an episode
        assert isinstance(self.file_object, BaseEpisode)

        result = self.config.get_key("filename_template")
        result = result.replace("<show>", self.file_object.show.name)
        result = result.replace("<season>", "%.2d" % \
            int(self.file_object.season.number))
        result = result.replace("<episode>", "%s" % \
            str(self.file_object.number))
        result = result.replace("<name>", self.file_object.name)
        for char in '\/:?*"<>|%.':
            result = result.replace(char, "_")
        result = result + ".mp4"

        return result

    def download_subtitle(self):
        """ Downloads the subtitle for the selected episode. """

        url = self.file_object.get_subtitle_url(quality=self.selected_quality)
        url_open = UrlOpen()

        url_open(url, filename=self.file_path.replace(".mp4", ".srt"))

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
        selected_text = self.hosts_icon_view_model[path][HOSTS_VIEW_COLUMN_TEXT]
        self.downloader = self.hosts_icon_view_model[path][HOSTS_VIEW_COLUMN_OBJECT]

        self.hosts_window.hide()

        self.selected_quality = selected_text.split("(")[1].split(")")[0]
        self.downloader.process_url(self.play, self.file_path)

    def _on_download_subtitle_finish(self, (is_error, result)):
        if is_error:
            log.error("Download subtitle failed: %s" % result)

            gobject.idle_add(self.gui_manager.set_status_message,
                gettext("Download subtitle failed"))
