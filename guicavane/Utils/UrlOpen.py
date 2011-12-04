#!/usr/bin/env python
# coding: utf-8

"""
UrlOpen

Requests webpages using cache, cookies,
headers and retry features.
"""

import time
import urllib
import socket
import httplib
import urllib2
import cookielib
import functools
from StringIO import StringIO

from Cached import Cached
from guicavane.Config import Config
from guicavane.Paths import CACHE_DIR
from guicavane.Utils.Log import console
from guicavane.Constants import DEFAULT_REQUEST_TIMEOUT, CUSTOM_DNS

log = console("GuiManager")
config = Config.get()

HEADERS = {
    'User-Agent': 'User-Agent:Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 '
                  '(KHTML, like Gecko) Chrome/13.0.772.0 Safari/535.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;'}

RETRY_TIMES = 5
cached = Cached.get()
cached.set_cache_dir(CACHE_DIR)

class DownloadError(Exception):
    """ Indicates a downloading error. """

def retry(callback):
    """ Retry decorator. """

    @functools.wraps(callback)
    def deco(*args, **kwargs):
        tried = 0

        while tried < RETRY_TIMES:
            try:
                return callback(*args, **kwargs)
            except Exception, error:
                urllib.urlcleanup()
                tried += 1
                time.sleep(1)


        error = "Can't download. Error: '%s'" % error
        long_error = error + ", args: '%s'" % (str(args) + str(kwargs))
        log.error(long_error)

        raise DownloadError(error)

    return deco


def CustomResolver(host):
    if config.get_key("use_custom_resolve"):
        if host in CUSTOM_DNS:
            host = CUSTOM_DNS[host]
    return host


class CustomHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        self.sock = socket.create_connection((CustomResolver(self.host),
                                              self.port), self.timeout)


class CustomHTTPHandler(urllib2.HTTPHandler, urllib2.HTTPCookieProcessor):
    def __init__(self, cookiejar):
        urllib2.HTTPHandler.__init__(self)
        urllib2.HTTPCookieProcessor.__init__(self, cookiejar)

    def http_open(self, req):
        return self.do_open(CustomHTTPConnection, req)


class UrlOpen(object):
    """ An url opener with cookies support. """

    def __init__(self, use_cache=True):
        self.cookiejar = cookielib.CookieJar()
        self.opener = self.build_opener()
        self.set_timeout(DEFAULT_REQUEST_TIMEOUT)
        self.use_cache = use_cache

    @retry
    def __call__(self, url, data=None, filename=None, handle=False, cache=True):
        cache_key = url + str(data)
        cache_data = cached(cache_key)

        if self.use_cache and cache and cache_data:
            return cache_data

        if data:
            request = urllib2.Request(url, urllib.urlencode(data), HEADERS)
        else:
            request = urllib2.Request(url, headers=HEADERS)

        rc = self.opener.open(request)

        # return file handler only
        if handle:
            return rc

        if filename:
            local = open(filename, "wb")
        else:
            local = StringIO()

        while True:
            buffer = rc.read(1024)

            if buffer == '':
                break

            local.write(buffer)

        if filename:
            local.close()
            return

        local.seek(0)

        data = local.read()

        if cache:
            # just cache if not a file
            cached(cache_key, data)

        return data

    def build_opener(self):
        """ Setup cookies in urllib2. """

        #handler = urllib2.HTTPCookieProcessor(self.cookiejar)
        handler = CustomHTTPHandler(self.cookiejar)
        return urllib2.build_opener(handler)

    def set_timeout(self, value):
        """ Sets the max request timeout. """

        socket.setdefaulttimeout(value)

    def add_cookies(self, cookies):
        """ Add new cookies. """

        for cookie in cookies:
            self.cookiejar.set_cookie(cookie)

    def add_headers(self, headers):
        """ Add new headers. headers argument has to be a diccionary. """

        base_headers = dict(self.opener.addheaders)
        base_headers.update(headers)
        self.opener.addheaders = base_headers.items()
