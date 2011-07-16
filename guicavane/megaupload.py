#!/usr/bin/env python
# coding: utf-8

"""
Megaupload.

Module that provides a thread to download megaupload files.
"""

import os
import re
import time
from threading import Thread

from pycavane.util import UrlOpen


MEGALINK_RE = re.compile('<a.*?href="(http://.*megaupload.*/files/.*?)"')
FILE_SIZE_RE = re.compile("<strong>(File size:|Tamaño del archivo:)</strong> (.+?) MB<br />")

URL_OPEN = UrlOpen()


class MegaFile(Thread):
    """
    Thread that downloads a megaupload file.
    """

    def __init__(self, url, cachedir, errback):
        Thread.__init__(self)
        self.url = url
        self.filename = url.rsplit('/', 1)[1][3:]
        self.cachedir = cachedir
        self.errback = errback
        self.running = True
        self.downloaded = False
        self.size = 0

    def get_megalink(self, link):
        """
        Returns the real file link after waiting the 45 seconds.
        """

        page_data = URL_OPEN(link)
        megalink = MEGALINK_RE.findall(page_data)
        self.size = FILE_SIZE_RE.search(page_data).group(2)

        if megalink:
            time.sleep(45)
            return megalink[0]

        return None

    @property
    def cache_file(self):
        """
        Returns the cache file path.
        """

        return self.cachedir + os.sep + self.filename + ".mp4"

    @property
    def downloaded_size(self):
        """
        Returns the size of the downloaded file at the moment.
        """

        size = 0
        if os.path.exists(self.cache_file):
            size = os.path.getsize(self.cache_file)
            size = size / 1024.0 / 1024.0  # In MB
        return size

    def run(self):
        """
        Starts the thread so starts the downloading.
        """

        self.downloaded = os.path.exists(self.cache_file)

        if not self.downloaded:
            url = self.get_megalink(self.url)
            try:
                handle = URL_OPEN(url, handle=True)
            except Exception, error:
                self.errback(error)
                return

            fd = open(self.cache_file, "wb")

            while True:
                data = handle.read(1024)

                if not data:
                    fd.close()
                    break

                fd.write(data)
                fd.flush()

        self.running = False
