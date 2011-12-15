#!/usr/bin/env python
# coding: utf-8

"""
Nooo API.
API for website www.nooo.tv

Authors: j0hn <j0hn.com.ar@gmail.com>
"""

import re
from hashlib import md5

import urls
from guicavane.Hosts.Base import *
from guicavane.Utils.Log import console
from guicavane.Utils.UrlOpen import UrlOpen

display_name = "Nooo"
display_image = "nooo.png"
implements = ["Movies"]

url_open = UrlOpen()
log = console("Hosts Noo")

HOSTMAP = {
    'http://bitshare.com': 'bitshare',
    'http://megaupload.com': 'megaupload',
}


class Episode(BaseEpisode):
    pass  # Not implemented


class Season(BaseSeason):
    pass  # Not implemented


class Show(BaseShow):
    pass  # Not implemented


class Movie(BaseMovie):
    _movies_re = re.compile('<h2><a href="(?P<url>.*?)" title="(?P<name>.*?)" ' \
                           'rel="bookmark">.*?</a></h2>')
    _link_url_re = re.compile('Descargar:<br /> <a href="(?P<url>.*?)" ' \
                              'onclick=".*?,.*?,\'(?P<host>.*?)\'\]\);">')
    _list_link_re = re.compile('<a href="(?P<url>.*?)".*?>(?P<host>.*?)</a>')
    _sub_url_re = re.compile('class="subtítulos" href="(.*?\.srt)">')

    _description_re = re.compile('<span class="dropCap">(.*?)</p>')
    _cast_re = re.compile('<p id="rxcast">Cast: (.*?)</p>')
    _image_re = re.compile('<img id="rxposter" src="(.*?)"')
    _genere_re = re.compile('<p id="rxgenres">Genre: (.*?)</p>')

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

    def get_subtitle_url(self, lang="ES", quality=None):
        data = url_open(self.url)

        sub_url = self._sub_url_re.search(data).group(1)
        return sub_url

    @property
    def original_url(self):
        return self.url

    @property
    def info(self):
        data = url_open(self.url)

        image = self._image_re.search(data).group(1)
        description = self._description_re.search(data).group(1).strip()
        description = description.replace("</span>", "")
        genere = self._genere_re.search(data).group(1).strip()
        language = ""
        cast = self._cast_re.search(data).group(1).split(",")

        info = {"image": image, "description": description,
                "cast": cast, "genere": genere, "language": language}

        return info

    @property
    def file_hosts(self):
        data = url_open(self.url)

        try:
            host = self._link_url_re.search(data).groupdict()
            result = {HOSTMAP[host["host"]]: {"360": host["url"]}}
            return result
        except:
            pass

        try:
            data = data.split('<div id="lista"><ul><li>')[1]
            data = data.split("</li>")[0]

            host = self._list_link_re.search(data).groupdict()
            result = {host["host"].lower(): {"360": host["url"]}}
            return result
        except:
            pass

        return {}

    @classmethod
    def search(cls, query=""):
        query = query.lower().replace(' ', '+')

        data = url_open(urls.search % query)

        for movie in cls._movies_re.finditer(data):
            movie_dict = movie.groupdict()

            # Invented ID
            movie_dict["id"] = int(md5(movie_dict["url"]).hexdigest(), 16)

            yield Movie(**movie_dict)

    @classmethod
    def get_recomended(cls):
        pass

    @classmethod
    def get_latest(cls):
        pass
