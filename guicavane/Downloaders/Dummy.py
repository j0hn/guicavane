#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import os
import time
import random

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader

class Dummy(BaseDownloader):
    """ Dummy's Downloader. """

    name = "Dummy"
    icon_path = HOSTS_IMAGES_DIR + SEP + "dummy.png"
    dummy_file = "/absolute/path/to/a/real/file"

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, None, gui_manager, url)

        self.gui_manager = gui_manager

        self.file_size = 100 * 1024 * 1024
        self._downloaded_size = 0

    @property
    def downloaded_size(self):
        return self._downloaded_size

    def process_url(self, play_callback, file_path):
        if not os.path.exists(file_path):
            os.symlink(self.dummy_file, file_path)

        self.gui_manager.background_task(self.simulate_download,
                    self.on_download_finish, unfreeze=False)

        play_callback()

    def simulate_download(self):
        while self.downloaded_size < self.file_size:
            time.sleep(1)
            speed = 300 + (100 * random.random())
            self._downloaded_size += speed * 1024

    def on_download_finish(self, *args):
        pass
