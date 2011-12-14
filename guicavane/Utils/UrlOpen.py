#!/usr/bin/env python
# coding: utf-8

"""
UrlOpen

Requests webpages using cache, cookies,
headers and retry features.
"""

import os
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
from guicavane.Paths import CACHE_DIR, COOKIES_FILE
from guicavane.Utils.Log import console
from guicavane.Constants import DEFAULT_REQUEST_TIMEOUT, CUSTOM_DNS

log = console("GuiManager")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.11 ' \
                  '(KHTML, like Gecko) Chrome/17.0.963.2 Safari/535.11',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

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

def save_cookies(callback):
    """ Save cookies in each request """

    @functools.wraps(callback)
    def deco(self, *args, **kwargs):
        data = callback(self, *args, **kwargs)
        self.cookiejar.save()
        return data

    return deco



def CustomResolver(host):
    config = Config.get()
    if config.get_key("use_custom_resolve"):
        if host in CUSTOM_DNS:
            host = CUSTOM_DNS[host]
    return host


class CustomHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        self.sock = socket.create_connection((CustomResolver(self.host),
                                              self.port), self.timeout)


class CustomHTTPHandler(urllib2.HTTPHandler):
    def __init__(self):
        urllib2.HTTPHandler.__init__(self)

    def http_open(self, req):
        return self.do_open(CustomHTTPConnection, req)

class UrlOpen(object):
    """ An url opener with cookies support. """

    def __init__(self, use_cache=True):
        self.cookiejar = cookielib.LWPCookieJar(filename=COOKIES_FILE)
        if os.path.exists(COOKIES_FILE):
            try:
                self.cookiejar.load()
            except:
                # Avoid corrupted cookies
                pass

        self.opener = self.build_opener()
        self.set_timeout(DEFAULT_REQUEST_TIMEOUT)
        self.use_cache = use_cache

    @retry
    @save_cookies
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

        cookie_handler = urllib2.HTTPCookieProcessor(self.cookiejar)
        custom_handler = CustomHTTPHandler()
        return urllib2.build_opener(cookie_handler, custom_handler)

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

    def check_cookie(self, domain):
        for cookie in self.cookiejar:
            if cookie.domain[1:] == domain and not cookie.is_expired():
                return True
        return False
