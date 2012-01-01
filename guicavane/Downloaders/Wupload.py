#!/usr/bin/env python
# coding: utf-8

"""
Wupload's Downloader.
"""

import re
import time
import gobject
import base64

from guicavane.Gettext import gettext
from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from guicavane.Utils.UrlOpen import UrlOpen, DownloadError
from guicavane.Config import Config
from guicavane.Accounts import ACCOUNTS
from CaptchaWindow import CaptchaWindow, CAPTCHA_IMAGE_PATH

from Base import BaseDownloader

from guicavane.Utils.Log import console
from guicavane.Utils.Debug import tmp_dump

log = console("Downloaders Wupload")


RECAPTCHA_CHALLENGE_URL = "http://api.recaptcha.net/challenge?k="
RECAPTCHA_IMAGE_URL = "http://www.google.com/recaptcha/api/image?c="

URL_ID_RE = re.compile(".*/file/(.*)/.*")
REGULAR_URL_RE = re.compile('href="(.*?\?start=1)"')
RECAPTCHA_CHALLENGE_ID_RE = re.compile('Recaptcha.create\("(.*?)"')
RECAPTCHA_NEW_CHALLENGE_RE = re.compile("challenge : '(.+?)',")
WAITING_TIME_RE = re.compile('var countDownDelay = (\d+);')
TM_RE = re.compile("id='tm' name='tm' value='(\d+)' />")
TM_HASH_RE = re.compile("id='tm_hash' name='tm_hash' value='(?P<value>[0-9a-f]*?)' />")
FILE_URL_RE = re.compile('<span>Download Ready </span></h3>.*?' \
                         '<p><a href="(.*?)">', re.DOTALL)
API_DOWNLOAD="http://api.wupload.com/link?method=getDownloadLink&u=%s&p=%s&ids=%s&redirect=true"
CAPTCHA_URL_OPEN = UrlOpen(use_cache=False)

ACCOUNT=ACCOUNTS["wupload"]

class Wupload(BaseDownloader):
    """ Wupload's Downloader. """

    name = "Wupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "wupload.png"
    accept_ranges = False

    def __init__(self, gui_manager, url):
        self.MAIN_URL_OPEN = UrlOpen(use_cache=False)

        self.config = Config.get()
        self.password = None
        self.user = None
        accounts = self.config.get_key("accounts")
        for t, v in accounts:
            if t != "wupload":
                continue
            self.user = v["username"]
            try:
                self.password = base64.b64decode(v["password"])
            except:
                pass
        BaseDownloader.__init__(self, self.MAIN_URL_OPEN, gui_manager, url)

        self.gui_manager = gui_manager
        self.url = url

        self.captcha_window = CaptchaWindow(gui_manager, self._on_captcha_ok)

        self.MAIN_URL_OPEN.add_headers({
            "Referer": url,
            "Origin": "http://www.wupload.com",
            "Host": "www.wupload.com",
        })

        CAPTCHA_URL_OPEN.add_headers({"referer": url})

    def process_url(self, play_callback, file_path):
        self.play_callback = play_callback
        self.file_path = file_path

        self.gui_manager.background_task(self.start_regular,
                        self.on_waiting_finish, unfreeze=False)

    def start_regular(self):
        if self.user and self.password and ACCOUNT.account_type=="Premium":
            console("trying with cool API")
            id_ = URL_ID_RE.search(self.url).group(1)
            self.file_url = API_DOWNLOAD % (self.user, self.password, id_)
            console(self.file_url)
            return False

        page_data = self.MAIN_URL_OPEN(self.url)
        try:
            self.regular_url = REGULAR_URL_RE.search(page_data).group(1)
            self.regular_url = "http://www.wupload.com/file/" + self.regular_url
        except Exception, e:
            msg = "Regular link not found"
            log.error(msg)
            log.error(e.message)
            tmp_dump(page_data, link)
            raise DownloadError(msg)

        self.MAIN_URL_OPEN.add_headers({"X-Requested-With": "XMLHttpRequest"})
        regular_data = self.MAIN_URL_OPEN(self.regular_url)


        if "countDownDelay" in regular_data:
            waiting_time = int(WAITING_TIME_RE.search(regular_data).group(1))

            try:
                tm = int(TM_RE.search(regular_data).group(1))
                tm_hash = TM_HASH_RE.search(regular_data).group("value")
                tm_data = {"tm": tm, "tm_hash": tm_hash}
            except:
                tm_data = None

            for i in range(waiting_time, 0, -1):
                gobject.idle_add(self.gui_manager.set_status_message,
                    gettext("Please wait %d second%s...") % (i, "s" * (i > 1)))
                time.sleep(1)

            log.info("Trying to get captcha..")
            log.info(tm_data)
            regular_data = self.MAIN_URL_OPEN(self.regular_url, data=tm_data)

        if "Download Ready" in regular_data:
            has_captcha = False
            self.file_url = FILE_URL_RE.search(regular_data).group(1)
        else:
            has_captcha = True

            try:
                self.recaptcha_challenge_id = RECAPTCHA_CHALLENGE_ID_RE.search(regular_data).group(1)
            except Exception, e:
                msg = "Captcha challenge not found!"
                log.error(msg)
                log.error(e.message)
                tmp_dump(page_data, self.url)
                raise DownloadError(msg)

        return has_captcha

    def on_waiting_finish(self, (is_error, result)):
        if is_error:
            message = gettext("Error obtaining wuploads's link: %s" % result)
            self.gui_manager.report_error(message)
            return
        else:
            has_captcha = result

            if not has_captcha:
                self._on_captcha_finish((False, None))
            else:
                self.gui_manager.background_task(self.request_captcha,
                    self.captcha_window.show)

        return None

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

        request_data = {
            "recaptcha_challenge_field": self.recaptcha_new_challenge,
            "recaptcha_response_field": response_text,
        }

        page_data = self.MAIN_URL_OPEN(self.regular_url, data=request_data)

        self.file_url = FILE_URL_RE.search(page_data).group(1)

    def _download_loop(self):
        handler = self.MAIN_URL_OPEN(self.file_url, handle=True)

        # Using the BaseDownloader download function
        self.download_to(handler, self.file_path)

    def _on_captcha_ok(self):
        self.gui_manager.background_task(self.send_captcha,
            self._on_captcha_finish)

    def _on_captcha_finish(self, (is_error, result)):
        if is_error:
            self.gui_manager.report_error(gettext("Wrong captcha"))
            return

        self.gui_manager.background_task(self._download_loop,
            self._on_download_finish)

        self.play_callback()

    def _on_download_finish(self, (is_error, result)):
        if is_error:
            message = gettext("Download finish with error: %s") % result
            self.gui_manager.report_error(message)

        self.gui_manager.unfreeze()
