#!/usr/bin/env python
# coding: utf-8

import time
import urllib
import urllib2
import cookielib
import functools

HEADERS = {
    'User-Agent': 'User-Agent:Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 '
                  '(KHTML, like Gecko) Chrome/13.0.772.0 Safari/535.1',
    'Referer': 'http://www.cuevana.tv/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;'}

RETRY_TIMES = 5


class Singleton(object):
    """
    Not really singleton but close taken from dx
    https://github.com/dequis/derpbot/blob/master/util.py
    """
    instance = None

    def __init__(self):
        if type(self).instance is not None:
            raise TypeError("Already instantiated, use .get()")
        type(self).instance = self

    @classmethod
    def get(cls):
        return cls.instance or cls()


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
    def __call__(self, url, data=None, filename=None, handle=False):
        if data:
            request = urllib2.Request(url, urllib.urlencode(data), HEADERS)
        else:
            request = urllib2.Request(url, headers=HEADERS)

        rc = self.opener.open(request)

        # return file handler only
        if handle:
            return rc

        local = None
        if filename:
            local = open(filename, 'wb')

        ret = ''

        while True:
            buffer = rc.read(1024)
            if buffer == '':
                break

            if local:
                local.write(buffer)
            else:
                ret += buffer

        if local:
            local.close()
            return

        return ret

    def setup_cookies(self):
        """
        Setup cookies in urllib2.
        """

        jar = cookielib.CookieJar()
        handler = urllib2.HTTPCookieProcessor(jar)
        self.opener = urllib2.build_opener(handler)
