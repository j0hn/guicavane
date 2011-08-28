#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import time
import gobject

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"
    waiting_time = 3

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager
        self.url = url

    def process_url(self, play_file):
        self.play_file = play_file
        self.gui_manager.background_task(self.wait_time,
                    self.start_download, unfreeze=False)

    def wait_time(self):
        for i in range(self.waiting_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d more seconds..." % i)
            time.sleep(1)

    def start_download(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            self.gui_manager.unfreeze()
            return

        self.play_file("path/to/file")
