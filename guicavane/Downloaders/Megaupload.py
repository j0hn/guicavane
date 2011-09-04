#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import re
import time
import gobject

from guicavane.util import UrlOpen
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader, DownloadError


MEGALINK_RE = re.compile('<a.*?href="(http://.*megaupload.*/files/.*?)"')
URL_OPEN = UrlOpen()


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url
        self.stop_downloading = False

        accounts = self.gui_manager.accounts
        self.account = accounts.get(self.name.lower())
        if self.account:
            URL_OPEN.add_cookies(self.account.cookiejar)

    def process_url(self, play_callback, file_path):
        """ Start the download process. """

        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.get_megalink,
                    self._on_megalink_finish, unfreeze=False)

    def wait_time(self):
        """ Waits the necesary time to start the download. """

        for i in range(self.account.wait_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d second%s..." % (i, "s" * (i > 1)))
            time.sleep(1)

    def start_download(self, (is_error, result)):
        """ Starts the actually download loop and opens up the player. """
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            return

        self.gui_manager.background_task(self._download_loop,
                    self._on_download_finish, unfreeze=False)

        self.play_callback()

    def get_megalink(self):
        """ Returns the real downloadable megaupload url. """
        try:
            page_data = URL_OPEN(self.url)
        except Exception, error:
            raise DownloadError(error)

        return MEGALINK_RE.findall(page_data)[0]

    def _on_megalink_finish(self, (is_error, result)):
        """ Called on finish finding the real link. """

        if is_error:
            self.gui_manager.report_error("Error obtaining megaupload's link: %s" % result)
            return

        self.megalink = result

        self.gui_manager.background_task(self.wait_time,
                    self.start_download, unfreeze=False)

    def _download_loop(self):
        """ Actually download the file. """

        try:
            handler = URL_OPEN(self.megalink, handle=True)
        except Exception, error:
            raise DownloadError("Error downloading from megaupload: %s" % error)

        # Using the BaseDownloader download function
        self.download_to(handler, self.file_path)

    def _on_download_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Download finish with error: %s" % result)

        self.gui_manager.unfreeze()
