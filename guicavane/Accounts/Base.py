#!/usr/bin/env python
# coding: utf-8

"""
Base Account. Every Account must be a subclass from this Account.
"""


class BaseAccount(object):
    """Base class for Account."""

    name = ""
    account_wait = {}

    def __init__(self):
        self.verified = False
        self.logged = False
        self.cookiejar = None
        self._account_type = None
        self._username = ""
        self._password = ""

    def login(self, username, password):
        """Verifies the account."""
        raise NotImplemented

    @property
    def account_type(self):
        """Account's membership."""
        raise NotImplemented

    @property
    def wait_time(self):
        """Wait time before downloading a file."""
        raise NotImplemented
