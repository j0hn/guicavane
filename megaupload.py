import os
import re
import time
from threading import Thread

import shutil
from util import UrlOpen


megalink_re = re.compile('<a.*?href="(http://.*megaupload.*/files/.*?)"')

url_open = UrlOpen()


class MegaFile(Thread):
    def __init__ (self, url, cachedir):
        Thread.__init__(self)
        self.url = url
        self.filename = url.rsplit('/', 1)[1]
        self.cachedir = cachedir
        self.released = False
        self.running = True

    def get_megalink(self, link):
        megalink = megalink_re.findall(url_open(link))
        if megalink:
            time.sleep(45)
            return megalink[0]
        return None

    @property
    def cache_file(self):
        filename = self.cachedir+'/'+self.filename
        if os.path.exists(filename+'.mp4'):
            return filename+'.mp4'
        return filename

    @property
    def size(self):
        size = 0
        if os.path.exists(self.cache_file):
            size = os.path.getsize(self.cache_file)
        return size

    def run(self):
        if not os.path.exists(self.cache_file):
            url = self.get_megalink(self.url)
            handle = url_open(url, handle=True)
            fd = open(self.cache_file, 'w')

            while True:
                if self.released:
                    # Remove file from cache if released
                    # before finish the download
                    os.remove(self.cache_file)
                    break
                data = handle.read(1024)
                if not data:
                    shutil.move(self.cache_file, self.cache_file+'.mp4')
                    fd.close()
                    break
                fd.write(data)
                fd.flush()
        self.running = False
