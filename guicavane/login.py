#!/usr/bin/env python
# encoding: utf-8

"""
Login.

Module that provides a handler for megaupload accounts.
"""

from urllib2 import HTTPCookieProcessor
from util import UrlOpen

ACCOUNT_WAIT = {None: 45,
                'Regular' : 25,
                'Premium' : 0}

URL_OPEN = UrlOpen()

LOGIN_PAGE = "http://www.megaupload.com?c=login"
ACCOUNT_PAGE = "http://www.megaupload.com?c=account"


class MegaAccount():
    """
    Megauplod account handler.
    """
    def __init__(self):
        self.verified = False
        self.logged = False
        self.cookiejar = None
        self._account_type = None

    def login(self, username, password):
        """
        Verifies the account.
        On succefull login, stores the cookie.
        """
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
    def member(self):
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
    def wait(self):
        """
        Megaupload waiting time for the given account.
        """
        return ACCOUNT_WAIT[self.member]
