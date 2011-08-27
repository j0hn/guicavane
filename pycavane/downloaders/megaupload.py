#!/usr/bin/env python
# coding: utf-8

"""
Megaupload.

Module that provides a thread to download megaupload files.
"""

import os
import re
import sys
import time

from util import url_open
from base import FileHost


MEGALINK_RE = re.compile('<a.*?href="(http://.*megaupload.*/files/.*?)"')
FILE_SIZE_RE = re.compile(
        "<strong>(File size:|Tamaño del archivo:)</strong> (.+?) MB<br />")


class MegauploadHost(FileHost):
    """
    Thread that downloads a megaupload file.
    """

    def __init__(self, id, cachedir='/tmp/', errback=None):
        FileHost.__init__(self, id, cachedir=cachedir, name='megaupload',
                                                          errback=errback)

        self.cachedir = cachedir
        self.errback = errback

        if not errback:
            self.errback = lambda err: sys.stdout.write(err)

        self.released = False
        self.running = True
        self.size = 0

    def get_megalink(self):
        """
        Returns the real file link after waiting the 45 seconds.
        """

        page_data = url_open(self.url)
        megalink = MEGALINK_RE.findall(page_data)
        self.size = FILE_SIZE_RE.search(page_data).group(2)

        if megalink:
            time.sleep(45)
            return megalink[0]
        return None

    def run(self):
        """
        Starts the thread so starts the downloading.
        """

        if not os.path.exists(self.cache_file):
            url = self.get_megalink()
            try:
                handle = url_open(url, handle=True)
            except Exception, error:
                self.errback(error)
                return

            fd = open(self.cache_file, 'wb')

            while True:
                if self.released:
                    # Remove file from cache if released
                    # before finish the download
                    os.remove(self.cache_file)
                    break
                data = handle.read(1024)
                if not data:
                    fd.close()
                    break
                fd.write(data)
                fd.flush()
        self.running = False
