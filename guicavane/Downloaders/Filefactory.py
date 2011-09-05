#!/usr/bin/env python
# coding: utf-8

"""
Filefactory Downloader.
"""

import re
import time
import gobject

from guicavane.util import UrlOpen
from Base import BaseDownloader
from CaptchaWindow import CaptchaWindow, CAPTCHA_IMAGE_PATH
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP

HOST = "http://www.filefactory.com"
RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="
CHECK_CAPTCHA_URL = HOST + "/file/checkCaptcha.php"

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
    accept_ranges = False

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, MAIN_URL_OPEN, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url

        self.captcha_window = CaptchaWindow(gui_manager, self._on_captcha_ok)

        CAPTCHA_URL_OPEN.add_headers({"referer": url})

    def process_url(self, play_callback, file_path):
        """ Start the download process. """

        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.request_captcha,
                    self.captcha_window.show, unfreeze=False)

    def request_captcha(self):
        page_data = CAPTCHA_URL_OPEN(self.url)
        self.captcha_id = CAPTCHA_ID_RE.search(page_data).group(1)
        self.check_id = CHECK_ID_RE.search(page_data).group(1)

        page_data = CAPTCHA_URL_OPEN(RECAPTCHA_CHALLENGE_URL + self.captcha_id)
        self.captcha_id2 = CAPTCHA_ID2_RE.search(page_data).group(1)

        image_url = RECAPTCHA_IMAGE_URL + self.captcha_id2
        page_data = CAPTCHA_URL_OPEN(image_url)
        filehandler = open(CAPTCHA_IMAGE_PATH, "wb")
        filehandler.write(page_data)
        filehandler.close()

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
            "Sending Captcha...")

        response_text = self.captcha_window.get_input_text()

        data = {"recaptcha_challenge_field": self.captcha_id2,
                "recaptcha_response_field": response_text,
                "recaptcha_shortencode_field": "undefined",
                "check": self.check_id}

        page_data = MAIN_URL_OPEN(CHECK_CAPTCHA_URL, data=data)

        assert page_data.count("status:\"ok\""), "Wrong captcha"

        file_pre_url = FILE_PRE_URL_RE.search(page_data).group(1)
        page_data = MAIN_URL_OPEN(HOST + file_pre_url)

        self.file_url = FILE_URL_RE.search(page_data).group(1)

        self.waiting_time = int(COUNTDOWN_RE.search(page_data).group(1))

    def _download_loop(self):
        for i in range(self.waiting_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d second%s..." % (i, "s" * (i > 1)))
            time.sleep(1)

        self.add_range(MAIN_URL_OPEN)
        handler = MAIN_URL_OPEN(self.file_url, handle=True)

        gobject.idle_add(self.gui_manager.set_status_message, "Loading...")

        # Using the BaseDownloader download function
        self.download_to(handler, self.file_path)

    def _on_captcha_ok(self, *args):
        self.gui_manager.background_task(self.send_captcha,
            self._on_captcha_finish)

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
