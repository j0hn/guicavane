#!/usr/bin/env python
# coding: utf-8

"""
Bitshare Downloader.
"""

import gtk
import time
import gobject

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"
    waiting_time = 5

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager
        self.url = url

    def process_url(self, play_file):
        self.play_file = play_file
        self.gui_manager.background_task(self.wait_time,
                        self.ask_captcha, unfreeze=False)

    def wait_time(self):
        for i in range(self.wait_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                             "Please wait %d more seconds..." % i)
            time.sleep(1)

    def ask_captcha(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            self.gui_manager.unfreeze()
            return

        gobject.idle_add(self.gui_manager.set_status_message,
                         "Please fill the captcha")

        self.captcha_window = gtk.Window()
        self.captcha_window.set_title("Please fill the captcha")
        btn = gtk.Button("CAPTCHA!")
        btn.connect("clicked", self._send_captcha)
        self.captcha_window.add(btn)
        self.captcha_window.show_all()

    def _send_captcha(self, button):
        self.captcha_window.hide()
        self.gui_manager.background_task(self.send_captcha, self.start_download)

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Sending Captcha...")
        time.sleep(3)

    def start_download(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            self.gui_manager.unfreeze()
            return

        self.play_file("path/to/file")
