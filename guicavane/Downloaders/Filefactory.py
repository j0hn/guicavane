#!/usr/bin/env python
# coding: utf-8

"""
Filefactory Downloader.
"""

import re
import gtk
import time
import gobject

from guicavane.util import UrlOpen
from Base import BaseDownloader, DownloadError
from guicavane.Constants import CAPTCHA_GUI_FILE
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP, TEMP_DIR

HOST = "http://www.filefactory.com"
RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="
CHECK_CAPTCHA_URL = HOST + "/file/checkCaptcha.php"

CAPTCHA_IMAGE_PATH = TEMP_DIR + SEP + "recaptcha_image"

CAPTCHA_ID_RE = re.compile(r'Recaptcha\.create\("(.*?)", "ffRecaptcha"')
CAPTCHA_ID2_RE = re.compile(r"challenge : '(.*?)',")
CHECK_ID_RE = re.compile(r"check:'(.*?)'")
FILE_PRE_URL_RE = re.compile(r'path:"(.*?)"')
FILE_URL_RE = re.compile(r'name="redirect" value="(.*?)"/>')
FILE_URL_RE = re.compile(r'<a href="(.*?)" id="downloadLinkTarget">')
COUNTDOWN_RE = re.compile(r'<span class="countdown">(\d*?)</span>')

MAIN_URL_OPEN = UrlOpen()
CAPTCHA_URL_OPEN = UrlOpen()


class Filefactory(BaseDownloader):
    """ Filefactory's Downloader. """

    name = "File Factory"
    icon_path = HOSTS_IMAGES_DIR + SEP + "filefactory.png"
    waiting_time = 60

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, gui_manager, url)

        CAPTCHA_URL_OPEN.add_headers({"referer": url})

        self.gui_manager = gui_manager
        self.url = url
        self.stop_downloading = False

        self.builder = gtk.Builder()
        self.builder.add_from_file(CAPTCHA_GUI_FILE)
        self.builder.connect_signals(self)

        self.captcha_image = self.builder.get_object("captcha_image")
        self.response_input = self.builder.get_object("response_input")
        self.captcha_window = self.builder.get_object("captcha_window")

    def process_url(self, play_callback, file_path):
        """ Start the download process. """

        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.request_captcha,
                    self.ask_captcha, unfreeze=False)

    def request_captcha(self):
        page_data = CAPTCHA_URL_OPEN(self.url)
        self.captcha_id = CAPTCHA_ID_RE.search(page_data).group(1)
        self.check_id = CHECK_ID_RE.search(page_data).group(1)

        page_data = CAPTCHA_URL_OPEN(RECAPTCHA_CHALLENGE_URL + self.captcha_id)
        self.captcha_id2 = CAPTCHA_ID2_RE.search(page_data).group(1)

        image_url = RECAPTCHA_IMAGE_URL + self.captcha_id2
        page_data = CAPTCHA_URL_OPEN(image_url)
        filehandler = open(CAPTCHA_IMAGE_PATH, "w")
        filehandler.write(page_data)
        filehandler.close()

    def ask_captcha(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error fetching captcha: %s" % result)
            return

        gobject.idle_add(self.gui_manager.set_status_message, "Please fill the captcha")

        self.captcha_image.set_from_file(CAPTCHA_IMAGE_PATH)
        self.captcha_window.show_all()

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
            "Sending Captcha...")

        response_text = self.response_input.get_text()

        data = {"recaptcha_challenge_field": self.captcha_id2,
                "recaptcha_response_field": response_text,
                "recaptcha_shortencode_field": "undefined",
                "check": self.check_id}

        page_data = MAIN_URL_OPEN(CHECK_CAPTCHA_URL, data=data)

        assert page_data.count("status:\"ok\""), "Wrong captcha"

        file_pre_url = FILE_PRE_URL_RE.search(page_data).group(1)
        page_data = MAIN_URL_OPEN(HOST + file_pre_url)

        self.file_url = FILE_URL_RE.search(page_data).group(1)

        try:
            self.waiting_time = int(COUNTDOWN_RE.search(page_data).group(1))
        except:
            pass

    def _download_loop(self):
        for i in range(self.waiting_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d second%s..." % (i, "s" * (i > 1)))
            time.sleep(1)

        handler = MAIN_URL_OPEN(self.file_url, handle=True)

        gobject.idle_add(self.gui_manager.set_status_message, "Loading...")
        # Using the BaseDownloader download function
        self.download_to(handler, self.file_path)

    def _on_captcha_ok(self, *args):
        self.gui_manager.background_task(self.send_captcha,
                                    self._on_captcha_finish)
        self.captcha_window.hide()

    def _on_captcha_cancel(self, *args):
        self.gui_manager.unfreeze()
        self.captcha_window.hide()

    def _on_captcha_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error: %s" % result)
            return

        self.gui_manager.background_task(self._download_loop,
            self._on_download_finish)

        self.play_callback()

    def _on_download_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Download finish with error: %s" % result)

        self.gui_manager.unfreeze()
