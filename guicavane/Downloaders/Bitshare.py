#!/usr/bin/env python
# coding: utf-8

"""
Bitshare Downloader.
"""

import re
import gtk
import time
import gobject

from Base import BaseDownloader, DownloadError
from guicavane.util import UrlOpen
from guicavane.Constants import CAPTCHA_GUI_FILE
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP


FILE_SIZE_RE = re.compile("<h1>Downloading.*? - (.*?)MByte</h1>")
AJAXDL_RE = re.compile('var ajaxdl = "(.*?)";')

REQUEST_URL = "http://bitshare.com/files-ajax/%s/request.html"

URL_OPEN = UrlOpen()


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url
        self.stop_downloading = True

        self.builder = gtk.Builder()
        self.builder.add_from_file(CAPTCHA_GUI_FILE)
        self.builder.connect_signals(self)

        self.captcha_window = self.builder.get_object("captcha_window")

    def process_url(self, play_callback, file_path):
        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.start_regular,
                        self.on_waiting_finish, unfreeze=False)

    def start_regular(self):
        try:
            page_data = URL_OPEN(self.url)
        except Exception, error:
            raise DownloadError(error)

        self.file_size = float(FILE_SIZE_RE.search(page_data).group(1)) * 1024 * 1024

        self.download_id = self.url.split("?f=")[1]
        self.ajaxdl = AJAXDL_RE.search(page_data).group(1)

        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "generateID", "ajaxid": self.ajaxdl}

        try:
            page_data = URL_OPEN(request_url, data=request_data)
        except Exception, error:
            raise DownloadError(error)

        page_data = page_data.split(":")
        waiting_time = int(page_data[1])
        has_captcha = page_data[2] == "1"

        for i in range(waiting_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d second%s..." % (i, "s" * (i > 1)))
            time.sleep(1)

        return has_captcha

    def on_waiting_finish(self, (is_error, result)):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Obtaining bitshare link...")

        if is_error:
            self.gui_manager.report_error("Error obtaining bitshare's link: %s" % result)
            self.gui_manager.unfreeze()
            return

        has_captcha = result

        if has_captcha:
            print "Not supported yet"
        else:
            self.gui_manager.background_task(self._download_loop,
                        self._on_download_finish)

            self.play_callback()

    def ask_captcha(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            self.gui_manager.unfreeze()
            return

        gobject.idle_add(self.gui_manager.set_status_message,
                         "Please fill the captcha")

        self.captcha_window.show_all()

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Sending Captcha...")
        time.sleep(3)

    def _download_loop(self):
        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "getDownloadURL", "ajaxid": self.ajaxdl}

        try:
            page_data = URL_OPEN(request_url, data=request_data)
        except Exception, error:
            raise DownloadError("Error downloading from bitshare: %s" % error)

        if not page_data.startswith("SUCCESS"):
            message = "Not success finding the bitshare "
            message += "download link. Got: %s" % page_data

            self.gui_manager.report_error(message)
            return

        real_link = page_data.split("#")[1]

        try:
            handle = URL_OPEN(real_link, handle=True)
        except Exception, error:
            raise DownloadError("Error downloading from bitshare: %s" % error)

        filehandler = open(self.file_path, "wb")

        while True:
            data = handle.read(1024)

            if not data or self.stop_downloading:
                filehandler.close()
                break

            filehandler.write(data)
            filehandler.flush()

    def _on_captcha_ok(self, button):
        self.gui_manager.background_task(self.send_captcha, self.start_download)
        self.captcha_window.hide()

    def _on_captcha_cancel(self, button):
        self.gui_manager.unfreeze()
        self.captcha_window.hide()

    def _on_download_finish(self, (is_error, result)):
        print "Downloading done"
