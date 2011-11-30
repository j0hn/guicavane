#!/usr/bin/env python
# coding: utf-8

"""
Cached

Module that provides a function to cache key, value data.
"""

import os
import time
try:
    import cPickle as pickle
except ImportError:
    import pickle

from singleton import Singleton


class Cached(Singleton):
    """
    Function that caches key, value data.

    The content of cache it's loadead and saved on a pickle file.
    """

    cache_dir = '/tmp/'
    lifetime = 60 * 60  # An hour in seconds
    __cache__ = None

    def __init__(self):
        Singleton.__init__(self)

    def set_cache_dir(self, cache_dir):
        """
        setup cache directory
        default: /tmp/
        """
        self.cache_dir = cache_dir

    def set_lifetime(self, lifetime):
        """
        setup lifetime in seconds
        default: 3600 (1 hour)
        """
        self.lifetime = lifetime

    @property
    def filename(self):
        fname = self.cache_dir + os.sep + '_cached_object'
        return fname

    @property
    def cache(self):
        """
        Open and unpickle the cache file or returns an empty dict if it fail
        """
        if self.__cache__ == None:
            try:
                with open(self.filename) as fd:
                    self.__cache__ = pickle.load(fd)
            except Exception, error:
                self.__cache__ = {}
        return self.__cache__

    def __call__(self, key, value=None):
        """
        Cache Function, if value it's None just try to return
        from cache or None if it dosn't exists.

        else set that value in cache
        """

        try:
            time_key = key + '_time'

            if key not in self.cache or \
                 self.cache[time_key] < time.time() - self.lifetime:

                if value is None:
                    return

                self.cache[key] = value
                self.cache[time_key] = time.time()
                with open(self.filename, 'w') as fd:
                    pickle.dump(self.cache, fd)
                return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return value

        return self.cache[key]
