#!/usr/bin/env python
# coding: utf-8

"""
Megaupload Downloader.
"""

import re

from guicavane.Util import UrlOpen
from Base import BaseAccount


LOGIN_PAGE = "http://www.megaupload.com?c=login"
ACCOUNT_PAGE = "http://www.megaupload.com?c=account"
URL_OPEN = UrlOpen()


class Megaupload(BaseAccount):
    """ Megaupload's Account. """

    name = "Megaupload"
    account_wait = {None: 45,
                    'Regular' : 25,
                    'Premium' : 0}

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

        self.verified = False

        self._username = username
        self._password = password

        data = {"login" : 1,
                "redir" : 1,
                "username" : username,
                "password" : password}

        rc = URL_OPEN(LOGIN_PAGE, data=data)
        if username in rc:
            self.logged = True
            self.cookiejar = URL_OPEN.cookiejar

        else:
            self.logged = False

        self.verified = True

    @property
    def account_type(self):
        """
        Account type: 'Regular', 'Premium' or None (if not logged).
        """
        if self.logged and not self._account_type:
            rc = URL_OPEN(ACCOUNT_PAGE)
            if 'upgrade' in rc:
                self._account_type = 'Regular'
            elif 'extend' in rc:
                self._account_type = 'Premium'
        return self._account_type

    @property
    def wait_time(self):
        """
        Megaupload waiting time for the given account.
        """
        return self.account_wait[self.account_type]

