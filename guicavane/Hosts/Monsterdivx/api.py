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

DISPLAY_NAME = "Monsterdivx"
url_open = UrlOpen()

HOST_TRANSLATE = {"mega": "megaupload",
                  "wupload": "wupload"}


class Episode(BaseEpisode):
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


class Movie(BaseMovie):
    _hosts_re = re.compile("onclick=\"goSource\('(?P<id>.*?)'," \
                           "'(?P<name>.*?)'\)")
    _real_id_re = re.compile("var postID = (.*?);")

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

    @classmethod
    def search(self, query=""):
        data = url_open(urls.search, data={"query": query})
        data = json.loads(data)
        for res in data:
            if "pelicula" in res["display"].lower():
                _id = res["id"]
                url = res["link"]
                name = res["value"]
                yield Movie(_id, name, url)

    @property
    def file_hosts(self):
        hosts = {}

        data = url_open(urls.host + '/' + self.url)
        _id = self._real_id_re.findall(data)[0]
        self.id = _id

        data = url_open(urls.sources % _id)
        data = data.split('<div id="sources">', 1)[1]
        data = data.split('<div style="clear:left">', 1)[0]

        for host in self._hosts_re.finditer(data):
            host = host.groupdict()

            args = {"key": host["id"],
                    "host": host["name"],
                    "id": _id,
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
