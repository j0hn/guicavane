#!/usr/bin/env python
# coding: utf-8

"""
Hotfile Downloader.
"""

import re
import time
import gobject

from Base import BaseDownloader
from guicavane.util import UrlOpen
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from CaptchaWindow import CaptchaWindow, CAPTCHA_IMAGE_PATH

RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="

TM_RE = re.compile(r'name=tm value=(.*?)>')
TMHASH_RE = re.compile(r'name=tmhash value=(.*?)>')
WAIT_RE = re.compile(r'<input type=hidden name=wait value=(\d*?)>')
WAITHASH_RE = re.compile(r'name=waithash value=(.*?)>')
UPIDHASH_RE = re.compile(r'name=upidhash value=(.*?)>')
CAPTCHA_ID_RE = re.compile(r'src="http://api.recaptcha.net/challenge\?k=(.*?)">')
CAPTCHA_ID2_RE = re.compile(r"challenge : '(.*?)',")
FILE_URL_RE = re.compile(r'href="(.*?)" class="click_download"')

MAIN_URL_OPEN = UrlOpen()
CAPTCHA_URL_OPEN = UrlOpen()


class Hotfile(BaseDownloader):
    """ Hotfile's Downloader. """

    name = "Hotfile"
    icon_path = HOSTS_IMAGES_DIR + SEP + "hotfile.png"
    accept_ranges = False

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, MAIN_URL_OPEN, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url

        self.captcha_window = CaptchaWindow(gui_manager, self._on_captcha_ok)

        CAPTCHA_URL_OPEN.add_headers({"referer": url})

    def process_url(self, play_callback, file_path):
        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.start_regular,
                        self.captcha_window.show, unfreeze=False)

    def start_regular(self):
        page_data = MAIN_URL_OPEN(self.url)

        waiting_time = int(WAIT_RE.search(page_data).group(1))
        tm = TM_RE.search(page_data).group(1)
        tmhash = TMHASH_RE.search(page_data).group(1)
        waithash = WAITHASH_RE.search(page_data).group(1)
        upidhash = UPIDHASH_RE.search(page_data).group(1)

        for i in range(waiting_time, 0, -1):
            gobject.idle_add(self.gui_manager.set_status_message,
                            "Please wait %d second%s..." % (i, "s" * (i > 1)))
            time.sleep(1)

        data = {"action": "capt", "tm": tm, "tmhash": tmhash,
                "wait": waiting_time, "waithash": waithash,
                "upidhash": upidhash}


        # Get the challenge id for the captcha request
        page_data = MAIN_URL_OPEN(self.url, data=data)
        captcha_id = CAPTCHA_ID_RE.search(page_data).group(1)

        # Get the challenge id for the captcha image
        page_data = CAPTCHA_URL_OPEN(RECAPTCHA_CHALLENGE_URL + captcha_id)
        self.captcha_id2 = CAPTCHA_ID2_RE.search(page_data).group(1)

        # Download the captcha image
        page_data = CAPTCHA_URL_OPEN(RECAPTCHA_IMAGE_URL + self.captcha_id2)
        filehandler = open(CAPTCHA_IMAGE_PATH, "wb")
        filehandler.write(page_data)
        filehandler.close()

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
            "Sending Captcha...")

        response_text = self.captcha_window.get_input_text()

        data = {"action": "checkcaptcha",
                "recaptcha_challenge_field": self.captcha_id2,
                "recaptcha_response_field": response_text}

        page_data = MAIN_URL_OPEN(self.url, data=data)
        self.file_url = FILE_URL_RE.search(page_data).group(1)

    def _download_loop(self):
        self.add_range(MAIN_URL_OPEN)
        handler = MAIN_URL_OPEN(self.file_url, handle=True)

        gobject.idle_add(self.gui_manager.set_status_message, "Loading...")

        # Using the BaseDownloader download function
        self.download_to(handler, self.file_path)

    def _on_captcha_ok(self):
        self.gui_manager.background_task(self.send_captcha,
            self._on_captcha_finish)

    def _on_captcha_finish(self, (is_error, result)):
        self.gui_manager.background_task(self._download_loop,
            self._on_download_finish)

        self.play_callback()

    def _on_download_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Download finish with error: %s" % result)

        self.gui_manager.unfreeze()
