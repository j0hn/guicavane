#!/usr/bin/env python
# coding: utf-8

import time
import thread
import gobject
import gtk

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"
    wait_time = 45

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager

    def process_url(self, play_file):
        """ Waits for the megauploads time. """

        self.play_file = play_file
        self.gui_manager.background_task(self.wait_time, self.start_download, unfreeze=False)

    def wait_time(self, play_file):
        for i in range(self.wait_time):
            gobject.idle_add(self.gui_manager.set_status_message, "waiting " + str(i))
            time.sleep(1)

        play_file("")

    def start_download(self, (is_error, result)):
        # TODO: fire a thread that starts the download

        self.play_file("path/to/file")
