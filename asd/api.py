#!/usr/bin/env python
# coding: utf-8

"""
Pycavane

A library to scrap the website www.cuevana.tv
Author: Roger Duran <rogerduran@gmail.com>
Contributor: j0hn <j0hn.com.ar@gmail.com>
"""

import re

import downloaders
from util import url_open, normalize_string
from cached import Cached

import urls


def setup(username=None, password=None,
        cache_dir='/tmp/', cache_lifetime=60*60*6):
    """
    Does the inicialization and login of the website.
    """

    # Singleton
    cached = Cached.get()
    cached.set_cache_dir(cache_dir)
    cached.set_lifetime(cache_lifetime)

    if username:
        data = {'usuario': username, 'password': password,
                'ingresar': True, 'recordarme': 'si'}
        ret = url_open(urls.login, data=data)
        if username not in ret:
            raise Exception('Login fail, check username and password')


class Episode(object):
    _search_re = re.compile('<li onclick=\'listSeries\(3,"(?P<id>[0-9]*)"\)\'>'\
                            '<span class=\'nume\'>(?P<number>.*?)'\
                            '</span>\s?(?P<name>.*?)</li>')

    _hosts_re = re.compile("goSource\('([a-zA-Z0-9]*?)','([a-zA-Z]*?)'\)")

    _name_re = re.compile(
            r'<div class="clearleft"></div>.*?</div>.*?: (.*?)</div>', re.DOTALL)
    _image_re = re.compile('<img src="(.*?)" border="0" />')
    _description_re = re.compile('<div>(.*)<div class="sep"></div>', re.DOTALL)
    _cast_re = re.compile('<a href=\'/buscar/\?q=.*?&cat=actor\'>(.*?)</a>')
    _genere_re = re.compile('<b>Género:</b>(.*?)<br />')
    _language_re = re.compile('<b>Idioma:</b>(.*?)<br />')

    __info = None
    __hosts = None
    __name = ''

    def __init__(self, id, number, name):
        self.id = id
        self.__name = name
        self.number = number

        info_keys = ['image', 'description', 'cast', 'genere', 'language']

        for info_key in info_keys:
            setattr(self.__class__, info_key,
                    property(lambda self, i=info_key:self.info[i]))

    @property
    def name(self):
        if self.__name.endswith('...'):
            return self.info['name']
        return self.__name

    @property
    def info(self):
        """
        set info data in __info dict and return it
        """

        if self.__info:
            return self.__info

        page_data = url_open(urls.show_info % self.id)
        print urls.show_info % self.id

        name = self._name_re.findall(page_data)[0].strip()
        image = urls.host + self._image_re.findall(page_data)[0]
        description = self._description_re.findall(page_data)[0].strip()
        cast = self._cast_re.findall(page_data)
        genere = self._genere_re.findall(page_data)[0].strip()
        language = self._language_re.findall(page_data)[0].strip()

        self.__info = {'name': name, 'image': image, 'description': description,
                'cast': cast, 'genere': genere, 'language': language}
        return self.__info

    @property
    def file_hosts(self):
        """
        Returns a a dict with name and instance
        """

        if self.__hosts:
            return self.__hosts

        self.__hosts = {}

        data = url_open(urls.player_season % self.id)
        for id, name in self._hosts_re.findall(data):
            class_name = name.title() + 'Host'
            if getattr(downloaders, class_name, None):
                # if implemented file host instance it
                host = getattr(downloaders, class_name)(id)
            else:
                # else return a generic one
                host = downloaders.FileHost(id, name=name)
            self.__hosts[name] = host

        return self.__hosts

    def get_subtitle(self, lang='ES', filename=None):
        """
        Downloads the subtitle of the episode.
        """

        if filename:
            filename += '.srt'

        return url_open(urls.sub_show % (self.id, lang), filename=filename)

    @classmethod
    def search(self, season):
        """
        Returns a list with Episodes of
        of `season`.
        """

        data = url_open(urls.episodes % season.id)
        for episode in self._search_re.finditer(data):
            yield Episode(**episode.groupdict())

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(object):
    _search_re = re.compile('<li onclick=\'listSeries'\
            '\(2,"(?P<id>[0-9]*)"\)\'>(?P<name>.*?)</li>')

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        """ Returs a list with the seasons from show. """

        data = url_open(urls.seasons % show.id)
        for season in self._search_re.finditer(data):
            yield Season(**season.groupdict())

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)


class Show(object):
    _search_re = re.compile('serieslist.push\(\{id:(?P<id>[0-9]*),nombre:'\
                          '"(?P<name>.*?)"\}\);')

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        """ Returns a list with Seasons """

        return Season.search(self)

    @property
    def description(self):
        raise NotImplementedError

    @classmethod
    def search(self, name=''):
        """ Returns a list with all the currently avaliable Shows. """

        name = name.lower()

        for show in self._search_re.finditer(url_open(urls.shows)):
            show_dict = show.groupdict()
            if not name or name in show_dict['name'].lower():
                yield Show(**show_dict)

    def __repr__(self):
        return '<Show: id: "%s" name: "%s">' % (self.id, self.name)


class Movie(object):
    _search_re = re.compile('<div class=\'tit\'>' \
                            '<a href=\'/peliculas/(?P<id>[0-9]*)/.*?\'>' \
                            '(?P<name>.*?) \((?P<year>[0-9]*)\)</a>' \
                            '</div>.*?<div class=\'txt\'>' \
                            '(?P<description>.*?)<div', re.DOTALL)
    _description_re = re.compile('<td class="infolabel" valign="top">Sinopsis</td>.*?' \
                                 '<td>(.+?)</td>', re.DOTALL)
    __info = ""

    def __init__(self, id, name, year=None, description=""):
        self.id = id
        self.name = name
        self.year = year
        self.__description = description

    @property
    def description(self):
        if self.__description.endswith('...'):
            return self.info['description']

        return self.__description

    @property
    def normalized_name(self):
        return normalize_string(self.name)

    @property
    def info(self):
        """
        Returns a dict with info about this movie
        """

        if self.__info:
            return self.__info

        page_data = url_open(urls.movie_info % (self.id, self.normalized_name))

        description = self._description_re.findall(page_data)[0].strip()
        # TODO: scrap the rest of the info

        self.__info = {'description': description}
        return self.__info

    @classmethod
    def search(self, query=""):
        """
        Returns a list with all the matched
        movies searched using the query
        """

        query = query.lower().replace(' ', '+')

        for movie in self._search_re.finditer(url_open(urls.search % query)):
            movie_dict = movie.groupdict()
            movie_dict['description'] = movie_dict['description'].strip()

            yield Movie(**movie_dict)

    def __repr__(self):
        return '<Movie id: "%s" name: "%s">' % (self.id, self.name)
