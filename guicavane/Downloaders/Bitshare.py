#!/usr/bin/env python
# coding: utf-8

import gtk
import time
import gobject

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"
    wait_time = 5

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager
        self.url = url

    def process_url(self, play_file):
        self.play_file = play_file
        self.gui_manager.background_task(self.wait_time, self.ask_captcha, unfreeze=False)

    def asd(self):
        time.sleep(3)
        return "j3j3j3j3"

    def wait_time(self):
        for i in range(self.wait_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                             "Please wait %d more seconds..." % i)
            time.sleep(1)

    def ask_captcha(self, (is_error, result)):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Please fill the captcha" % i)

        win = gtk.Window()
        win.set_title("Please fill the captcha")
        btn = gtk.Button("CAPTCHA!")
        btn.connect("clicked", self.send_captcha)
        win.add(btn)
        win.show_all()

    def send_captcha(self, button):
        print "sending captcha"
        self.play_file("path/to/file/")
