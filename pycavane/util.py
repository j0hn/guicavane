import time
import urllib
import urllib2
import cookielib
import functools


class Singleton(object):
    '''Not really singleton but close
    taken from dx https://github.com/dequis/derpbot/blob/master/util.py'''
    instance = None

    def __init__(self):
        if type(self).instance is not None:
            raise TypeError("Already instantiated, use .get()")
        type(self).instance = self

    @classmethod
    def get(cls):
        return cls.instance or cls()


headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; '\
                           'rv:1.9.2.10) Gecko/20100928 Firefox/3.6.1'}

def retry(callback):
    ''' Retry decorator '''

    @functools.wraps(callback)
    def deco(*args, **kwargs):
        tried = 0
        while tried < 10:
            try:
                return callback(*args, **kwargs)
            except Exception, error:
                tried += 1
                time.sleep(1)
        error = 'Can\'t download\nerror: "%s"\n args: %s' % \
                            (error, str(args) + str(kwargs))
        raise Exception, error
    return deco


class UrlOpen(object):
    ''' An url opener with cookies support '''
    def __init__(self):
        self.setup_cookies()

    @retry
    def __call__(self, url, data=None, filename=None, handle=False):
        if data:
            request = urllib2.Request(url, urllib.urlencode(data), headers)
        else:
            request = urllib2.Request(url, headers=headers)

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
        ''' Setup cookies in urllib2 '''
        jar = cookielib.CookieJar()
        handler = urllib2.HTTPCookieProcessor(jar)
        self.opener = urllib2.build_opener(handler)
