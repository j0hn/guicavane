#!/usr/bin/env python
# coding: utf-8

import re
import urllib
from hashlib import md5

import moviezet_urls as urls
from util import url_open, normalize_string
from base_api import Episode as BaseEpisode, \
                     Show as BaseShow, \
                     Season as BaseSeason, \
                     Movie as BaseMovie

HOSTMAP = {'megaupload': 'http://www.megaupload.com/?d=',
           'kickupload': 'http://www.kickupload.com/files/',
           'bitshare': 'http://bitshare.com/?f=',
           'filefactory': 'http://www.filefactory.com/file/'
           }
HOSTNAMES = {'mega': 'megaupload',
            'kick': 'kickupload',
            'bits': 'bitshare',
            'file': 'filefactory'}


class Episode(BaseEpisode):
    _search_re =  re.compile('<a href="(?P<id>.*?)" title="(?P<number>[0-9]*?)"'\
                             '.*?</b>(?P<name>.*?)</a>')
    _watch_url = re.compile('<a class="watch-show" href="(.*?)">')

    #<a href="#7698" title="1"><b>1.</b> It's alive</a></li>

    _hosts_re = re.compile('<a href="/getvid.php\?id=(?P<id>(.*?))&'\
                           'name=(.*?)&server=(?P<host>.*?)".*?>')
    __hosts = None

    def __init__(self, id, number, name, show, season):
        self.id = id
        self.season = season
        self.show = show
        self.__name = name
        self.number = number

    @property
    def name(self):
        return self.__name

    @property
    def info(self):
        raise NotImplementedError

    @property
    def file_hosts(self):
        if self.__hosts:
            return self.__hosts
        self.__hosts = {}

        data = url_open(urls.episode % (urllib.quote(self.show),
                                        self.season, self.number))
        watch_url = self._watch_url.findall(data)[0]

        data = url_open(watch_url)

        for host in self._hosts_re.finditer(data):
            host_dict = host.groupdict()
            hostname = HOSTNAMES[host_dict["host"]]
            url = HOSTMAP[hostname] + host_dict["id"]
            self.__hosts[hostname] = url

        return self.__hosts

    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        url =  urls.sub_show % (self.id.replace("#", ""), lang)
        try:
            result = url_open(url, filename=filename)
        except Exception:
            raise Exception("Subtitle not found")

        return result

    @classmethod
    def search(self, season):
        """
        Returns a list with Episodes of
        of `season`.
        """

        url = urls.episodes % (urllib.quote(season.show), season.id)
        data = url_open(url).split('<ol id="episode-list">')[1]

        for episode in self._search_re.finditer(data):
            episode_dict = episode.groupdict()
            episode_dict.update(dict(show=season.show,
                                      season=season.id))
            yield Episode(**episode_dict)

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(BaseSeason):
    _search_re = re.compile('<a(.*?)title="(?P<id>[0-9]*?)">'\
                            '(?P<name>.*?)</a>')
    def __init__(self, id, name, show):
        self.id = id
        self.name = name
        self.show = show

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        data = url_open(urls.seasons % urllib.quote(show.name))
        data = data.split('<ol id="season-list">')[1]

        for season in self._search_re.finditer(data):
            season_dict = season.groupdict()
            season_dict["show"] = show.name
            yield Season(**season_dict)

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)

class Show(BaseShow):
    _search_re = re.compile('<a(.*?)>(?P<name>.*?)</a>')
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        """
        Returns a list with Seasons
        """
        return Season.search(self)

    @classmethod
    def search(self, name=''):
        """
        Returns a list with all the
        currently avaliable Shows
        """

        name = name.lower()
        data = url_open(urls.shows)

        for show in self._search_re.finditer(data):
            show_dict = show.groupdict()
            show_dict["id"] = int(md5(show_dict["name"]).hexdigest(), 16)
            if not name or name in  show_dict["name"].lower():
                yield Show(**show_dict)

    def __repr__(self):
        return '<Show: name: "%s">' % self.name

class Movie(BaseMovie):
    pass

