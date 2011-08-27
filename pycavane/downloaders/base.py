import re
from threading import Thread

import urls
from util import url_open


class FileHost(Thread):
    _search_re = re.compile("goSource\('([a-zA-Z0-9]*?)','([a-zA-Z]*?)'\)")
    __url = None

    def __init__(self, id, name, cachedir='/tmp/', errback=None):
        Thread.__init__(self)
        self.id = id
        self.name = name
        self.cachedir = cachedir

    @property
    def url(self):
        if not self.__url:
            data = [('key', self.id), ('host', self.name), 
                    ('vars', '&id=9555&subs=,ES,EN&tipo=s&amp;sub_pre=ES')]
            url = url_open(urls.source_get, data=data)
            # before http are ugly chars
            self.__url = url[url.find('http:'):].split('&id')[0]
        return self.__url

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

    @property
    def filename(sefl):
        """
        Returns the filename based on the url
        """
        return self.url.rsplit('/', 1)[1]

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
        raise NotImplementedError

    @property
    def run(self):
        """
        Starts the thread so starts the downloading.
        """
        raise NotImplementedError
