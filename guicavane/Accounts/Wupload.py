#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import re
import json

from guicavane.Utils.UrlOpen import UrlOpen
from guicavane.Utils.Debug import tmp_dump
from guicavane.Utils.Log import console
from Base import BaseAccount

log = console("Accounts.Wupload")

LOGIN_PAGE = "http://www.wupload/account/login"
ACCOUNT_PAGE = "http://www.wupload/account/settings"
CHECK_STATUS = "http://api.wupload.com/user?method=getInfo&format=json&u=%s&p=%s"
URL_OPEN = UrlOpen(use_cache=False)

class Wupload(BaseAccount):
    """ Wupload's Account. """

    name = "Wupload"
    account_wait = {None: 60,
                    'Regular' : 60,
                    'Premium' : 0}
    premium = False

    def __init__(self):
        BaseAccount.__init__(self)

    def login(self, username, password):
        """
        Verifies the account.
        On succefull login, stores the cookie.
        """

        if self._username == username and \
            self._password == password:
            return
        url = CHECK_STATUS % ( username, password )

        self.verified = False
        self.premium = False

        self._username = username
        self._password = password

        rc = URL_OPEN(url)
        reply = json.loads(rc)
        for i in ['FSApi_User', 'getInfo']:
            if not i in reply:
                log.warn("Invalid response, doesn't contain %s" % i)
                log.info(repr(reply))
                return
            reply = reply[i]

        if reply["status"].lower() != "success":
            log.warn("Invalid status %s" % reply["status"])
            return

        log.info("loged in successfully")
        user = reply["response"]["users"]["user"]
        self.premium = user["is_premium"]
        log.info("is premium %s" % self.premium)
        self.verified = True
        self.logged = True

    @property
    def account_type(self):
        """
        Account type: 'Regular', 'Premium' or None (if not logged).
        """
        if self.logged and not self._account_type:
            self._account_type = "Premium" if self.premium else "Regular"
        return self._account_type

    @property
    def wait_time(self):
        """
        Megaupload waiting time for the given account.
        """
        return self.account_wait[self.account_type]
