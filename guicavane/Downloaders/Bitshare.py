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
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP, TEMP_DIR


FILE_SIZE_RE = re.compile("<h1>Downloading.*? - (.*?)MByte</h1>")
AJAXDL_RE = re.compile('var ajaxdl = "(.*?)";')

REQUEST_URL = "http://bitshare.com/files-ajax/%s/request.html"

RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="

RECAPTCHA_CHALLENGE_ID_RE = re.compile('<script type="text/javascript" ' \
                     'src="http://api.recaptcha.net/challenge\?k=(.+?) ">')
RECAPTCHA_NEW_CHALLENGE_RE = re.compile("challenge : '(.+?)',")

CAPTCHA_IMAGE_PATH = TEMP_DIR + SEP + "recaptcha_image"

URL_OPEN = UrlOpen()
URL_OPEN2 = UrlOpen()


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"

    def __init__(self, gui_manager, url):
        BaseDownloader.__init__(self, gui_manager, url)

        URL_OPEN2.add_headers({"referer": url})

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
            self.gui_manager.background_task(self.request_captcha,
                        self.ask_captcha)
        else:
            self.gui_manager.background_task(self._download_loop,
                        self._on_download_finish)

            self.play_callback()

    def request_captcha(self):

        try:
            page_data = URL_OPEN2(RECAPTCHA_CHALLENGE_URL + self.recaptcha_challenge_id)
        except Exception, error:
            raise DownloadError("Error obtaining recaptcha challenge: %s" % error)

        self.recaptcha_new_challenge = RECAPTCHA_NEW_CHALLENGE_RE.search(page_data).group(1)
        image_url = RECAPTCHA_IMAGE_URL + self.recaptcha_new_challenge

        try:
            page_data = URL_OPEN2(image_url)
        except Exception, error:
            raise DownloadError("Error obtaining recaptcha image: %s" % error)

        filehandler = open(CAPTCHA_IMAGE_PATH, "w")
        filehandler.write(page_data)
        filehandler.close()

    def ask_captcha(self, (is_error, result)):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Please fill the captcha")

        self.captcha_image.set_from_file(CAPTCHA_IMAGE_PATH)
        self.captcha_window.show_all()


    def send_captcha(self):
        gobject.idle_add(self.gui_manager.set_status_message,
                         "Sending Captcha...")

        response_text = self.response_input.get_text()

        request_url = REQUEST_URL % self.download_id
        request_data = {"request": "validateCaptcha", "ajaxid": self.ajaxdl,
            "recaptcha_challenge_field": self.recaptcha_new_challenge,
            "recaptcha_response_field": response_text}

        try:
            page_data = URL_OPEN(request_url, data=request_data)
        except Exception, error:
            raise DownloadError("Error sending captcha: %s" % error)

        return page_data.count("SUCCESS") > 0

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

    def _on_captcha_ok(self, *args):
        self.gui_manager.background_task(self.send_captcha,
                                    self._on_captcha_finish)
        self.captcha_window.hide()

    def _on_captcha_cancel(self, *args):
        self.gui_manager.unfreeze()
        self.captcha_window.hide()

    def _on_captcha_finish(self, (is_error, result)):
        self.gui_manager.background_task(self._download_loop,
                    self._on_download_finish)

        self.play_callback()

    def _on_download_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error("Error downloading: %s" % result)

        print "Downloading done"
