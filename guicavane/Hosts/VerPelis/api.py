#!/usr/bin/env python
# coding: utf-8

"""
Ver-Pelis API.
API for website www.ver-pelis.net

Authors: Andres Bordese <andresb9163@gmail.com>
"""

import re
from hashlib import md5

from guicavane.Hosts.Base import *
import urls
from guicavane.Utils.UrlOpen import UrlOpen

DISPLAY_NAME = "Ver-Pelis"

url_open = UrlOpen()


def normalize_name(name):
    name = name.replace('.', ' ').replace(':', '').replace('&', '')
    name = name.strip().replace(' ', '-')
    # Replacing characters could produce double '-'
    while '--' in name:
        name = name.replace('--', '-')

    return name.lower()


class Episode(BaseEpisode):
    _hosts_re = re.compile('<a.*?title="Ver pelicula desde (?P<host>[^\?"]*?)\??"'\
                           '.*?href="(?P<id>.*?)vp=.*?">')
    _serie_info_re = re.compile('<div class="peli_img_int mgbot10px">.*?'\
                                '<img src="(?P<image>.*?)".*?/>.*?</div>.*?'\
                                'Genero:</span> (?P<genere>.*?)</li>.*'\
                                '<div class="sinoptxt.*?">.*?<p>'\
                                '(?P<description>.*?)</p>', re.DOTALL)

    def __init__(self, id, name, number, season, show):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show

        self.__hosts = {}

    @property
    def file_hosts(self):
        # Cache
        if self.__hosts:
            return self.__hosts

        data = url_open(urls.episode % (normalize_name(self.show.name),
                                        self.season.number, self.number))

        for host in self._hosts_re.finditer(data):
            host_dict = host.groupdict()
            hostname = host_dict["host"].lower()
            url = host_dict["id"]

            if not hostname in self.__hosts:
                self.__hosts[hostname] = {}

            self.__hosts[hostname]["360"] = url

        return self.__hosts

    @property
    def original_url(self):
        return urls.episode_orig_url % (normalize_name(self.show.name),
                                       self.season.number, self.number)

    @property
    def info(self):
        url = urls.episode_orig_url % (normalize_name(self.show.name),
                                        self.season.number, self.number)
        data = url_open(url)

        info = self._serie_info_re.search(data).groupdict()
        # Adding missing fields
        info['cast'] = ''
        info['language'] = ''
        # Making pretty some fields
        info['description'] = info['description'].strip()

        return info

    def get_subtitle_url(self, lang="ES", quality=None):
        # Notar, la pagina no tiene soporte para diferentes idiomas
        return urls.sub_show % (normalize_name(self.show.name),
                                self.season.number, self.number)


class Season(BaseSeason):
    _episodes_re = re.compile('<li><a.*?title=".*?x(?P<number>[0-9]*?)".*?'\
            'href="(?P<id>.*?)".*?><strong>(?P<name>.*?)</strong></a></li>')
    _episodes_delimiter = '<div id="lista">'

    def __init__(self, id, name, number, show):
        self.id = id
        self.name = name
        self.number = number
        self.show = show

    @property
    def episodes(self):
        url = urls.episodes % (normalize_name(self.show.name), normalize_name(self.id))
        data = url_open(url)

        data = data.split(self._episodes_delimiter)[1]

        for episode in self._episodes_re.finditer(data):
            episode_dict = episode.groupdict()
            episode_dict["season"] = self
            episode_dict["show"] = self.show

            yield Episode(**episode_dict)


class Show(BaseShow):
    _shows_re = re.compile('<li><a([^<>]*?)>(?P<name>[^<>]*?)</span></a></li>')
    _seasons_re = re.compile('<li><a(.*?)title="(?P<id>[^<>]*?)" .*?>'\
                             '<strong>(?P<name>.*?)</strong></a></li>')

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        data = url_open(urls.seasons % normalize_name(self.name))

        for number, season in enumerate(self._seasons_re.finditer(data)):
            season_dict = season.groupdict()
            season_dict["id"] = season_dict["id"].replace(self.name, '').strip()
            season_dict["number"] = number + 1
            season_dict["show"] = self

            name = season_dict["name"].replace(self.name, "").strip()
            season_dict["name"] = name

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
    pass
