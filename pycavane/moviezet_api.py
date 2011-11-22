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


class Episode(object):
    _search_re =  re.compile('<a href="(?P<id>.*?)" title="(?P<number>[0-9]*?)"'\
                             '.*?</b>(?P<name>.*?)</a>')
    _watch_url = re.compile('<a class="watch-show" href="(.*?)">')

    #<a href="#7698" title="1"><b>1.</b> It's alive</a></li>

    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')
    _host_names_re = re.compile('class="server" alt="(?P<name>.*?)"')

    def __init__(self, id, number, name):
        self.id = id
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
        data = url_open(urls.episode % (urllib.quote(self.show.name), self.season.id, self.number))
        watch_url = self._watch_url.findall(data)[0]

        self.__hosts = {}

        data = url_open(watch_url)
        hostnames = self._host_names_re.findall(data)

        hostmap = {'megaupload': 'http://www.megaupload.com/?d=',
                   'bitshare': 'http://bitshare.com/?f=',
                   'filefactory': 'http://www.filefactory.com/file/'
                   }

        for name, id in self._hosts_re.findall(data):
            self.__hosts['megaupload'] = hostmap.get('megaupload')+id
            break
            if not hostnames:
                break
            hostname = hostnames.pop()
            id = hostmap.get(hostname, '') + id
            self.__hosts[hostname] = id

        print self.__hosts
        return self.__hosts

    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        id = self.id.split('/play/')[1].split('/', 1)[0]
        print
        print urls.sub_show % id
        print "asdas adsas dads asd asdada<<<<<<<<<<<<<<<<<<<<<<<<<"
        try:
            result = url_open(urls.sub_show % id, filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    @classmethod
    def search(self, season):
        """
        Returns a list with Episodes of
        of `season`.
        """

        data = url_open(urls.episodes % (urllib.quote(season.show.name), season.id))
        data = data.split('<ol id="episode-list">')[1]

        for episode in self._search_re.finditer(data):
            e =  Episode(**episode.groupdict())
            e.show = season.show
            e.season = season
            yield e

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(BaseSeason):
    _search_re = re.compile('<a(.*?)title="(?P<id>[0-9]*?)">'\
                            '(?P<name>.*?)</a>')
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.show = None

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        data = url_open(urls.seasons % urllib.quote(show.name))
        data = data.split('<ol id="season-list">')[1]

        for season in self._search_re.finditer(data):
            s =  Season(**season.groupdict())
            s.show = show
            yield s

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

        data = url_open(urls.shows)

        for show in self._search_re.finditer(data):
            show_dict = show.groupdict()
            show_dict["id"] = int(md5(show_dict["name"]).hexdigest(), 16)

            yield Show(**show_dict)

    def __repr__(self):
        return '<Show: name: "%s">' % self.name

class Movie(BaseMovie):
    pass

