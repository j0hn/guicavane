#!/usr/bin/env python
# coding: utf-8

"""
Pelispedia API.
API for website www.pelispedia.com

Authors: Roger Duran <rogerduran@gmail.com>
"""

import re

import urls
from guicavane.Hosts.Base import *
from guicavane.Utils.UrlOpen import UrlOpen

display_name = "Pelispedia"
display_image = "pelispedia.png"
implements = ["Shows", "Movies"]

HOSTMAP = {'megaupload': 'http://www.megaupload.com/?d=',
           'kickupload': 'http://www.kickupload.com/files/',
           'bitshare': 'http://bitshare.com/?f=',
           'filefactory': 'http://www.filefactory.com/file/',
           'hotfile': 'http://hotfile.com/dl/',
           }

HOSTNAMES = {'mega1': 'megaupload',
            'mega2': 'bitshare',
            'mega3': 'filefactory',
            'mega4': 'hotfile',
            'mega5': 'wupload',
            'mega6': 'glumbo',
            'mega7': 'uploadhere',
            'mega8': 'uploadking',
            }


url_open = UrlOpen()


class Resource(BaseResource):
    __hosts = None

    @property
    def file_hosts(self):

        # Cache
        if self.__hosts:
            return self.__hosts
        self.__hosts = {}

        data = url_open(self.url)

        for name, id in self._hosts_re.findall(data):
            if not id:
                continue

            hostname = HOSTNAMES[name]
            if hostname not in HOSTMAP:
                continue

            if hostname not in self.__hosts:
                self.__hosts[hostname] = {}

            self.__hosts[hostname]["360"] = HOSTMAP[hostname] + id

        return self.__hosts


class Episode(Resource, BaseEpisode):
    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')

    def __init__(self, id, name, number, season, show, url):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show
        self.url = url

    def get_subtitle_url(self, lang="ES", quality=None):
        return urls.sub_show % self.id


class Season(BaseSeason):
    _episodes_re = re.compile("<option value='(?P<url>.*?)'>(?P<number>[0-9]*?)" \
                              " - (?P<name>.*?)</option>")

    def __init__(self, id, name, number, show):
        self.id = id
        self.name = name
        self.number = number
        self.show = show

    @property
    def episodes(self):
        data = url_open(urls.episodes, {'ss': self.show.id,
                                        't': self.id})
        for episode in self._episodes_re.finditer(data):
            episode_dict = episode.groupdict()
            episode_dict["show"] = self.show
            episode_dict["season"] = self
            episode_dict["id"] = episode_dict["url"].split('/play/')[1].split('/', 1)[0]
            yield Episode(**episode_dict)


class Show(BaseShow):
    _shows_re = re.compile('<option value="(?P<id>[0-9]*?)">'\
                            '(?P<name>.*?)</option>')
    _seasons_re = re.compile('<option value=\'(?P<id>[0-9]*?)\'>'\
                            '(?P<name>.*?)</option>')

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        data = url_open(urls.seasons, {'s': self.id})

        for season in self._seasons_re.finditer(data):
            season_dict = season.groupdict()
            season_dict["number"] = season_dict["id"]
            season_dict["show"] = self

            yield Season(**season_dict)

    @classmethod
    def search(self, name=''):
        name = name.lower()

        data = url_open(urls.shows)
        data = data.split('<select name="s" id="serie" size="15">')[1]
        data = data.split('</select>', 1)[0]

        for show in self._shows_re.finditer(data):
            show_dict = show.groupdict()
            if not name or name in show_dict['name'].lower():
                yield Show(**show_dict)


class Movie(Resource, BaseMovie):
    _search_re = re.compile('<div class="titletip"><b><a '\
            'href="(?P<url>.*?)">(?P<name>.*?)</a></b></div>')
    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')
    _host_names_re = re.compile('class="server" alt="(?P<name>.*?)"')

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

    @classmethod
    def search(self, query=""):
        query = query.lower().replace(' ', '+')

        data = url_open(urls.movies % query)

        for movie in self._search_re.finditer(data):
            movie_dict = movie.groupdict()
            movie_dict["id"] = movie_dict["url"].split('/play/')[1].split('/', 1)[0]
            yield Movie(**movie_dict)

    def get_subtitle_url(self, lang="ES", quality=None):

        id1, id2 = self.url.split('/play/')[1].split('/', 1)[0].split("-")
        id = "%s-%s" % (id2, id1)

        return urls.sub_movie % id
