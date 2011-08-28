#!/usr/bin/env python
# coding: utf-8

import time
import thread
import gobject

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"

    def __init__(self, gui_manager, url):
        self.gui_manager = gui_manager

    def process_url(self, done_callback):
        """ Waits for the megauploads time. """

        thread.start_new_thread(self.wait_time, (done_callback,))

    def wait_time(self, done_callback):
        for i in range(10):
            gobject.idle_add(self.gui_manager.set_status_message, "waiting " + str(i))
            time.sleep(1)

        done_callback("")
