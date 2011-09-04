#!/usr/bin/env python
# coding: utf-8

"""
Bitshare Downloader.
"""

import re
import time
import gobject

from Base import BaseDownloader, DownloadError
from guicavane.util import UrlOpen
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from CaptchaWindow import CaptchaWindow, CAPTCHA_IMAGE_PATH


AJAXDL_RE = re.compile('var ajaxdl = "(.*?)";')

REQUEST_URL = "http://bitshare.com/files-ajax/%s/request.html"

RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="

RECAPTCHA_CHALLENGE_ID_RE = re.compile('<script type="text/javascript" ' \
                     'src="http://api.recaptcha.net/challenge\?k=(.+?) ">')
RECAPTCHA_NEW_CHALLENGE_RE = re.compile("challenge : '(.+?)',")

MAIN_URL_OPEN = UrlOpen()
CAPTCHA_URL_OPEN = UrlOpen()


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url

        self.captcha_window = CaptchaWindow(gui_manager, self._on_captcha_ok)

        CAPTCHA_URL_OPEN.add_headers({"referer": url})

    def process_url(self, play_callback, file_path):
        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.start_regular,
                        self.on_waiting_finish, unfreeze=False)

    def start_regular(self):
        page_data = MAIN_URL_OPEN(self.url)
        self.download_id = self.url.split("?f=")[1]

        try:
            self.ajaxdl = AJAXDL_RE.search(page_data).group(1)
        except:
            raise DownloadError("ajaxid not found")

        try:
            self.recaptcha_challenge_id = RECAPTCHA_CHALLENGE_ID_RE.search(page_data).group(1)
        except:
            print "Captcha id not found"
            self.recaptcha_challenge_id = None

        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "generateID", "ajaxid": self.ajaxdl}

        page_data = MAIN_URL_OPEN(request_url, data=request_data)
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
            return

        has_captcha = result

        if has_captcha:
            self.gui_manager.background_task(self.request_captcha,
                self.captcha_window.show)
        else:
            self.gui_manager.background_task(self._download_loop,
                self._on_download_finish)

            self.play_callback()

    def request_captcha(self):
        assert self.recaptcha_challenge_id != None, "Captcha required but challenge not found"

        page_data = CAPTCHA_URL_OPEN(RECAPTCHA_CHALLENGE_URL + self.recaptcha_challenge_id)
        self.recaptcha_new_challenge = RECAPTCHA_NEW_CHALLENGE_RE.search(page_data).group(1)
        image_url = RECAPTCHA_IMAGE_URL + self.recaptcha_new_challenge

        page_data = CAPTCHA_URL_OPEN(image_url)
        filehandler = open(CAPTCHA_IMAGE_PATH, "wb")
        filehandler.write(page_data)
        filehandler.close()

    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
            "Sending Captcha...")

        response_text = self.captcha_window.get_input_text()

        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "validateCaptcha", "ajaxid": self.ajaxdl,
            "recaptcha_challenge_field": self.recaptcha_new_challenge,
            "recaptcha_response_field": response_text}

        page_data = MAIN_URL_OPEN(request_url, data=request_data)
        return page_data.count("SUCCESS") > 0

    def _download_loop(self):
        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "getDownloadURL", "ajaxid": self.ajaxdl}

        page_data = MAIN_URL_OPEN(request_url, data=request_data)

        if not page_data.startswith("SUCCESS"):
            message = "Not success finding the bitshare "
            message += "download link. Got: %s" % page_data

            self.gui_manager.report_error(message)
            return

        real_link = page_data.split("#")[1]

        handler = MAIN_URL_OPEN(real_link, handle=True)

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
