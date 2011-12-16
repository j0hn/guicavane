#!/usr/bin/env python
# coding: utf-8

"""
Monsterdivx API.
API for website www.monsterdivx.com


Authors: j0hn <j0hn.com.ar@gmail.com>
"""

import re
import json

import urls
from guicavane.Hosts.Base import *
from guicavane.Utils.UrlOpen import UrlOpen

display_name = "Monsterdivx"
display_image = "monsterdivx.png"
implements = ["Shows", "Movies", "Recomended", "Latest"]

url_open = UrlOpen()

HOST_TRANSLATE = {"mega": "megaupload",
                  "wupload": "wupload"}


def _match_or_empty_string(re_obj, data, group):
    try:
        return re_obj.search(data).group(group)
    except:
        return ""


class Resource(BaseResource):
    _image_re = re.compile('<div class=".*?trailer-img.*?">.*?'\
                           '<img.*?src="(.*?)".*?/> ', re.DOTALL)
    _description_re = re.compile('<h4>Sinopsis</h4>.*?' \
                                 '<div class="block">(.*?)</div>', re.DOTALL)
    _cast_re = re.compile('<a href=".*?/actores/.*?">(.*?)</a>')
    _genere_re = re.compile('<span>Género</span>.*?>(.*?)<')

    @property
    def info(self):
        data = url_open(self.original_url)

        image = _match_or_empty_string(self._image_re, data, 1)

        data = data.split('<div class="information">')[1]

        description = _match_or_empty_string(self._description_re, data, 1).strip()
        cast = self._cast_re.findall(data)
        genere = _match_or_empty_string(self._genere_re, data, 1).strip()
        language = ""

        info = {"image": image, "description": description,
                "cast": cast, "genere": genere, "language": language}

        return info

    @property
    def original_url(self):
        return "%s/%s" % (urls.host, self.slug)


class Episode(Resource, BaseEpisode):
    _hosts_re = re.compile("onclick=\"goSource\('(?P<id>.*?)'," \
                           "'(?P<name>.*?)'\)")

    def __init__(self, id, name, number, season, show, slug):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show
        self.slug = slug

    @property
    def file_hosts(self):
        hosts = {}

        data = url_open(urls.sources % self.id)
        data = data.split('<div id="sources">', 1)[1]
        data = data.split('<div style="clear:left">', 1)[0]

        for host in self._hosts_re.finditer(data):
            host = host.groupdict()

            args = {"key": host["id"],
                    "host": host["name"],
                    "id": self.id,
                    "sub": ",ES",
                    "sub_pre": "ES"}

            hostdata = url_open(urls.source_get, args)

            longname = HOST_TRANSLATE[host["name"]]

            if longname not in hosts:
                hosts[longname] = {}

            hosts[longname]["360"] = hostdata

        return hosts

    def get_subtitle_url(self, lang="ES", quality=None):
        return urls.sub_show % (self.id, lang)


class Season(BaseSeason):

    def __init__(self, id, name, number, show, slug):
        self.id = id
        self.name = name
        self.number = number
        self.show = show
        self.slug = slug

    @property
    def episodes(self):
        data = url_open(urls.episodes % self.id)
        jsondata = json.loads(data)

        for episode in jsondata:
            id = episode["id"]
            name = episode["name"]
            number = int(episode["capitulo"])
            slug = episode["slug"]
            yield Episode(id, name, number, self, self.show, slug)


class Show(BaseShow):
    _shows_re = re.compile('<a href="(?P<url>.*?)" rel="(?P<id>\d+)".*?>' \
                           '(?P<name>.*?)</a>')

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

    @property
    def seasons(self):
        data = url_open(urls.seasons % self.id)
        jsondata = json.loads(data)

        for season in jsondata:
            id = season["term_id"]
            name = season["name"]
            number = int(name.replace("Temporada", ""))
            slug = season["slug"]
            yield Season(id, name, number, self, slug)

    @classmethod
    def search(self, name=""):
        name = name.lower()

        data = url_open(urls.shows)
        data = data.split('<ul id="first-col">', 1)[1]
        data = data.split('</ul>', 1)[0]

        for show in self._shows_re.finditer(data):
            show_dict = show.groupdict()
            if not name or name in show_dict['name'].lower():
                yield Show(**show_dict)


class Movie(Resource, BaseMovie):
    _hosts_re = re.compile("onclick=\"goSource\('(?P<id>.*?)'," \
                           "'(?P<name>.*?)'\)")
    _real_id_re = re.compile("var postID = (.*?);")
    _recomended_movies_re = re.compile('<h2><a href="(?P<url>.*?)">' \
                                       '(?P<name>.*?)</a></h2>')

    def __init__(self, id, name, slug):
        self._id = id
        self.name = name
        self.slug = slug

    @classmethod
    def search(self, query=""):
        data = url_open(urls.search, data={"query": query})
        data = json.loads(data)
        for res in data:
            if "pelicula" in res["display"].lower():
                _id = None #res["id"]
                slug = res["link"]
                name = res["value"]
                yield Movie(_id, name, slug)

    @property
    def id(self):
        if not self._id:
            data = url_open(self.original_url)
            _id = self._real_id_re.findall(data)[0]
            self._id = _id
        return self._id

    @property
    def file_hosts(self):
        hosts = {}

        data = url_open(urls.sources % self.id)
        data = data.split('<div id="sources">', 1)[1]
        data = data.split('<div style="clear:left">', 1)[0]

        for host in self._hosts_re.finditer(data):
            host = host.groupdict()

            args = {"key": host["id"],
                    "host": host["name"],
                    "id": self.id,
                    "sub": ",ES",
                    "sub_pre": "ES"}

            hostdata = url_open(urls.source_get, args)

            longname = HOST_TRANSLATE[host["name"]]

            if longname not in hosts:
                hosts[longname] = {}

            hosts[longname]["360"] = hostdata

        return hosts

    def get_subtitle_url(self, lang="ES", quality=None):
        return urls.sub_show % (self.id, lang)

    @classmethod
    def get_latest(cls):
        return cls._get_movies_from_url(urls.latest_movies)

    @classmethod
    def get_recomended(cls):
        return cls._get_movies_from_url(urls.recomended_movies)

    @classmethod
    def _get_movies_from_url(cls, url):
        data = url_open(url)
        data = data.split("<h2>LISTADO DE PELICULAS</h2>")[1]

        for movie in cls._recomended_movies_re.finditer(data):
            movie = movie.groupdict()

            _id = None
            name = movie["name"]
            slug = movie["url"].replace(urls.host, "")
            yield Movie(_id, name, slug)
