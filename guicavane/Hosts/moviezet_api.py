#!/usr/bin/env python
# coding: utf-8

"""
Moviezet API.
API for website www.moviezet.com

Authors: Roger Duran <rogerduran@gmail.com>
         j0hn <j0hn.com.ar@gmail.com>
"""

import re
import urllib
from hashlib import md5

from base import *
import moviezet_urls as urls
from guicavane.Utils.UrlOpen import UrlOpen

HOSTMAP = {'megaupload': 'http://www.megaupload.com/?d=',
           'kickupload': 'http://www.kickupload.com/files/',
           'bitshare': 'http://bitshare.com/?f=',
           'filefactory': 'http://www.filefactory.com/file/'
           }
HOSTNAMES = {'mega': 'megaupload',
             'kick': 'kickupload',
             'bits': 'bitshare',
             'file': 'filefactory'}

DISPLAY_NAME = "Moviezet"

url_open = UrlOpen()


class Episode(BaseEpisode):
    _watch_url = re.compile('<a class="watch-show" href="(.*?)">')

    _hosts_re = re.compile('<a href="/getvid.php\?id=(?P<id>(.*?))&'\
                           'name=(.*?)&server=(?P<host>.*?)".*?>')
    __hosts = {}

    def __init__(self, id, name, number, season, show):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show

    @property
    def file_hosts(self):
        # Cache
        if self.__hosts:
            return self.__hosts

        data = url_open(urls.episode % (urllib.quote(self.show.name),
                                        self.season.id, self.number))
        watch_url = self._watch_url.findall(data)[0]
        data = url_open(watch_url)

        for host in self._hosts_re.finditer(data):
            host_dict = host.groupdict()
            hostname = HOSTNAMES[host_dict["host"]]
            url = HOSTMAP[hostname] + host_dict["id"]

            if not hostname in self.__hosts:
                self.__hosts[hostname] = {}

            self.__hosts[hostname]["360"] = url

        return self.__hosts

    def get_subtitle(self, lang="ES", quality=None):
        return urls.sub_show % (self.id.replace("#", ""), lang)


class Season(BaseSeason):
    _episodes_re = re.compile('<a href="(?P<id>.*?)" title='\
            '"(?P<number>[0-9]*?)".*?</b>(?P<name>.*?)</a>')

    def __init__(self, id, name, number, show):
        self.id = id
        self.name = name
        self.number = number
        self.show = show

    @property
    def episodes(self):
        url = urls.episodes % (urllib.quote(self.show.name), self.id)
        data = url_open(url).split('<ol id="episode-list">')[1]

        for episode in self._episodes_re.finditer(data):
            episode_dict = episode.groupdict()
            episode_dict["season"] = self
            episode_dict["show"] = self.show

            yield Episode(**episode_dict)


class Show(BaseShow):
    _shows_re = re.compile('<a(.*?)>(?P<name>.*?)</a>')
    _seasons_re = re.compile('<a(.*?)title="(?P<id>[0-9]*?)">'\
                             '(?P<name>.*?)</a>')

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        data = url_open(urls.seasons % urllib.quote(self.name))
        data = data.split('<ol id="season-list">')[1]

        for season in self._seasons_re.finditer(data):
            season_dict = season.groupdict()
            season_dict["number"] = season_dict["id"]
            season_dict["show"] = self
            yield Season(**season_dict)

    @classmethod
    def search(self, name=''):
        name = name.lower()
        data = url_open(urls.shows)

        for show in self._shows_re.finditer(data):
            show_dict = show.groupdict()
            show_dict["id"] = int(md5(show_dict["name"]).hexdigest(), 16)
            if not name or name in show_dict["name"].lower():
                yield Show(**show_dict)


class Movie(BaseMovie):
    _search_re = re.compile('div class="movie-thumb">\n<a href="'\
            '(?P<url>.*?)/" title="(?P<name>.*?)">')
    _hosts_re = re.compile('<a href="/getvid.php\?id=(?P<id>(.*?))&'\
                           'name=(.*?)&server=(?P<host>.*?)".*?>')
    _id_re = re.compile("href='http://www.moviezet.com/\?p=(?P<id>.*?)'")

    __hosts = {}

    def __init__(self, id, name, url):
        self.id = id
        if name.startswith("Ver ") and name.endswith(" Online"):
            name = name[4:-7]
        self.name = name
        self.url = url

    @classmethod
    def search(self, query=""):
        query = query.lower().replace(' ', '+')
        data = url_open(urls.movies_search % query)

        for movie in self._search_re.finditer(data):
            movie_dict = movie.groupdict()
            movie_dict["id"] = None
            yield Movie(**movie_dict)

    @property
    def file_hosts(self):
        # Cache
        if self.__hosts:
            return self.__hosts

        data = url_open(urls.movie % self.id)

        for host in self._hosts_re.finditer(data):
            host_dict = host.groupdict()
            hostname = HOSTNAMES[host_dict["host"]]
            url = HOSTMAP[hostname] + host_dict["id"]

            if hostname not in self.__hosts:
                self.__hosts[hostname] = {}

            self.__hosts[hostname]["360"] = url

        return self.__hosts

    def get_subtitle(self, lang="ES", quality=None):
        self.id = self._id_re.search(url_open(self.url)).group(1)
        return urls.sub_show % (self.id, lang)
