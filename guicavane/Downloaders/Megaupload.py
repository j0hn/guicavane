#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import re
import time
import gobject

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from guicavane.util import UrlOpen
from Base import BaseDownloader, DownloadError


MEGALINK_RE = re.compile('<a.*?href="(http://.*megaupload.*/files/.*?)"')
URL_OPEN = UrlOpen()


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"
    waiting_time = 45

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager
        self.url = url

    def process_url(self, play_callback, file_path):
        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.get_megalink,
                    self._on_megalink_finish, unfreeze=False)

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

        self.gui_manager.background_task(self._download_loop,
                    self._on_download_finish, unfreeze=False)

        self.play_callback()

    def get_megalink(self):
        try:
            page_data = URL_OPEN(self.url)
        except Exception, error:
            raise DownloadError(error)

        return MEGALINK_RE.findall(page_data)[0]

    def _on_megalink_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error obtaining megaupload's link: %s" % result)
            self.gui_manager.unfreeze()
            return

        self.megalink = result

        self.gui_manager.background_task(self.wait_time,
                    self.start_download, unfreeze=False)

    def _download_loop(self):
        try:
            handle = URL_OPEN(self.megalink, handle=True)
        except Exception, error:
            raise DownloadError("Error downloading from megaupload: %s" % error)

        filehandler = open(self.file_path, "wb")

        while True:
            data = handle.read(1024)

            if not data:
                filehandler.close()
                break

            filehandler.write(data)
            filehandler.flush()

    def _on_download_finish(self, (is_error, result)):
        print "Downloading done"
