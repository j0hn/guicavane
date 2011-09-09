#!/usr/bin/env python
# coding: utf-8

import time
import urllib
import urllib2
import cookielib
import functools
from StringIO import StringIO
from unicodedata import normalize

from cached import Cached

cached = Cached.get()

HEADERS = {
    'User-Agent': 'User-Agent:Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 '
                  '(KHTML, like Gecko) Chrome/13.0.772.0 Safari/535.1',
    'Referer': 'http://www.cuevana.tv/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;'}

RETRY_TIMES = 5


def normalize_string(string):
    """
    Take a string and return a cleaned string ready to use for cuevana
    """

    repl_list = [(" ", "-"), (".", ""), (",", ""),
                 ("'", ""), ("?", ""), ("$", ""),
                 ("#", ""), ("*", ""), ("!", ""),
                 (":", "")]

    uni_str = unicode(string, "utf-8")
    clean_str = normalize("NFKD", uni_str).encode("ASCII", "ignore").lower()

    for combo in repl_list:
        clean_str = clean_str.replace(combo[0], combo[1])

    return clean_str


def retry(callback):
    """
    Retry decorator.
    """

    @functools.wraps(callback)
    def deco(*args, **kwargs):
        tried = 0
        while tried < RETRY_TIMES:
            try:
                return callback(*args, **kwargs)
            except Exception, error:
                # Try to fix problens with squid
                urllib.urlcleanup()
                tried += 1
                time.sleep(1)
        error = 'Can\'t download\nerror: "%s"\n args: %s' % \
                            (error, str(args) + str(kwargs))
        raise Exception(error)
    return deco


class UrlOpen(object):
    """
    An url opener with cookies support.
    """

    def __init__(self):
        self.setup_cookies()

    @retry
    def __call__(self, url, data=None, filename=None, handle=False, cache=True):
        cache_key = url+str(data)

        cache_data = cached(cache_key)
        if cache and cache_data:
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
            local = open(filename, 'wb')
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

    def setup_cookies(self):
        """
        Setup cookies in urllib2.
        """

        jar = cookielib.CookieJar()
        handler = urllib2.HTTPCookieProcessor(jar)
        self.opener = urllib2.build_opener(handler)

url_open = UrlOpen()
