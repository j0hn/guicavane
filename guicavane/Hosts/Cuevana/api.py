#!/usr/bin/env python
# coding: utf-8

"""
Cuevana API.
API for website www.cuevana.tv

Authors: Roger Duran <rogerduran@gmail.com>
         j0hn <j0hn.com.ar@gmail.com>
"""

import re
import json

import urls
from guicavane.Hosts.Base import *
from guicavane.Utils.UrlOpen import UrlOpen

DISPLAY_NAME = "Cuevana"
url_open = UrlOpen()


class Episode(BaseEpisode):
    _sources_re = re.compile('sources = ({.*?}), sel_source')
    _image_re = re.compile('<div class="img"><img src="(.*?)" /></div>')
    _description_re = re.compile('<h2>Sinopsis</h2>(.*?)<div class="sep">', re.DOTALL)
    _cast_re = re.compile("<a href='#!/buscar/actor:.*?'>(.*?)</a>")
    _genere_re = re.compile('<b>Género:</b>(.*?)</div>')
    _language_re = re.compile('<b>Idioma:</b>(.*)</div>')

    __info = None
    __hosts = {}

    def __init__(self, id, name, number, season, show, url):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show
        self.url = url

        self.urlname = self.url.rsplit("/", 1)[-1]

    def get_subtitle_url(self, lang="ES", quality=None):
        if quality:
            return urls.sub_show_quality % (self.id, lang, quality)

        return urls.sub_show % (self.id, lang)

    @property
    def info(self):

        # Cache
        if self.__info:
            return self.__info

        page_data = url_open(urls.show_info % \
            (self.id, self.show.urlname, self.urlname))

        image = self._image_re.search(page_data).group(1)
        description = self._description_re.search(page_data).group(1).strip()
        cast = self._cast_re.findall(page_data)
        genere = self._genere_re.search(page_data).group(1).strip()
        language = self._language_re.search(page_data).group(1).strip()

        self.__info = {"image": image, "description": description,
                       "cast": cast, "genere": genere, "language": language}

        return self.__info

    @property
    def file_hosts(self):

        # Cache
        if self.__hosts:
            return self.__hosts

        data = url_open(urls.show_sources % self.id)
        sources = json.loads(self._sources_re.search(data).group(1))

        for quality in sources:
            for host in sources[quality]["2"]:
                data = [("id", self.id), ("tipo", "serie"),
                        ("def", quality), ("audio", "2"),
                        ("host", host)]

                hostdata = url_open(urls.source_get, data=data)
                url = hostdata[hostdata.find('http:'):].split('&id')[0]

                if not host in self.__hosts:
                    self.__hosts[host] = {}

                self.__hosts[host][quality] = url

        return self.__hosts

    @property
    def original_url(self):
        """ Returns the link to this episode on cuevana. """

        return urls.host + "/" + self.url


class Season(BaseSeason):
    def __init__(self, id, name, number, show, episodes):
        self.id = id
        self.name = name
        self.number = number
        self.show = show

        self._episodes = episodes

    @property
    def episodes(self):
        for ep in self._episodes:
            yield Episode(ep["id"], ep["tit"], ep["num"],
                          self, self.show, ep["url"])


class Show(BaseShow):
    _shows_json_re = re.compile("'#list'\).list\(\{l:(.*?]), page:", re.DOTALL)
    _seasons_json_re = re.compile("serieList\({l:({.*?}),e", re.DOTALL)

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url
        self.urlname = self.url.rsplit("/", 1)[-1]

    @property
    def seasons(self):
        data = url_open(urls.seasons % (self.id, self.urlname))
        jsondata = json.loads(self._seasons_json_re.search(data).group(1))

        for number in sorted(jsondata, key=lambda k: int(k)):
            episodes = jsondata[number]
            name = "Temporada %s" % number

            yield Season(number, name, number, self, episodes)

    @classmethod
    def search(cls, name=""):
        name = name.lower()

        data = url_open(urls.shows)
        jsondata = json.loads(cls._shows_json_re.search(data).group(1))

        for show in jsondata:
            if not name or name in show['tit'].lower():
                yield Show(show["id"], show["tit"], show["url"])


class Movie(BaseMovie):
    _search_re = re.compile("\$\('#list'\).list\({l:(.*?), set:\[")
    _sources_re = re.compile('sources = ({.*?}), sel_source')

    _image_re = re.compile('<div class="img"><img src="(.*?)" />')
    _description_re = re.compile('<h2>Sinopsis</h2>(.*?)<div class="sep">', re.DOTALL)
    _cast_re = re.compile("<a href='#!/buscar/q:.*?'>(.*?)</a>")
    _genere_re = re.compile('<b>Género:</b>(.*?)</div>')
    _language_re = re.compile('<b>Idioma:</b>(.*?)</div>')

    __info = ""
    __hosts = {}

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url
        self.urlname = self.url.rsplit("/", 1)[-1]

    def get_subtitle_url(self, lang="ES", quality=None):
        if quality:
            return urls.sub_movie_quality % (self.id, lang, quality)

        return urls.sub_movie % (self.id, lang)

    @property
    def original_url(self):
        return urls.host + "/" + self.url

    @property
    def info(self):

        # Cache
        if self.__info:
            return self.__info

        page_data = url_open(urls.movie_info % (self.id, self.urlname))

        image = self._image_re.search(page_data).group(1)
        description = self._description_re.search(page_data).group(1).strip()
        genere = self._genere_re.search(page_data).group(1).strip()
        language = self._language_re.search(page_data).group(1).strip()

        # Set because it's twice on the webpage
        cast = list(set(self._cast_re.findall(page_data)))

        self.__info = {"image": image, "description": description,
                       "cast": cast, "genere": genere, "language": language}

        return self.__info

    @property
    def file_hosts(self):

        # Cache
        if self.__hosts:
            return self.__hosts

        data = url_open(urls.movie_sources % self.id)
        sources = json.loads(self._sources_re.search(data).group(1))

        for quality in sources:
            for host in sources[quality]["2"]:
                data = [("id", self.id), ("tipo", "pelicula"),
                        ("def", quality), ("audio", "2"),
                        ("host", host)]

                hostdata = url_open(urls.source_get, data=data)
                url = hostdata[hostdata.find('http:'):].split('&id')[0]

                if not host in self.__hosts:
                    self.__hosts[host] = {}

                self.__hosts[host][quality] = url

        return self.__hosts

    @classmethod
    def search(self, query=""):
        query = query.lower().replace(' ', '+')

        data = url_open(urls.search % query)
        data = json.loads(self._search_re.search(data).group(1))

        for movie in data:
            if not "#!/peliculas" in movie["url"]:
                continue

            yield Movie(movie["id"], movie["tit"], movie["url"])
