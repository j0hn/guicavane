#!/usr/bin/env python
# coding: utf-8

"""
Pycavane

A library to scrap the website www.cuevana.tv
Author: Roger Duran <rogerduran@gmail.com>
Contributor: j0hn <j0hn.com.ar@gmail.com>
"""

import re

from util import UrlOpen
from memo import Memoized


HOST = 'http://www.cuevana.tv'

MOVIES_URL = HOST + '/peliculas/lista/letra=%s&page=%s'
SERIES_URL = HOST + '/series/'
SEASSONS_URL = HOST + '/list_search_id.php?serie=%s'
EPISODES_URL = HOST + '/list_search_id.php?temporada=%s'

EPISODE_URL = HOST + '/series/%s/%s/%s/'
PLAYER_MOVIE_URL = HOST + '/player/source?id=%s'
PLAYER_SEASON_URL = PLAYER_MOVIE_URL + '&tipo=s'
SOURCE_GET = HOST + '/player/source_get'

SUB_URL_MOVIE = HOST + '/files/sub/%s_%s.srt'
SUB_URL_SHOW = HOST + '/files/s/sub/%s_%s.srt'

SEARCH_URL = HOST + '/buscar/?q=%s&cat=titulo'


SERIES_RE = re.compile('serieslist.push\(\{id:([0-9]*),nombre:"(.*?)"\}\);')
SEASSON_RE = re.compile('<li onclick=\'listSeries\(2,"([0-9]*)"\)\'>(.*?)</li>')
EPISODE_RE = re.compile('<li onclick=\'listSeries\(3,"([0-9]*)"\)\'>'\
                        '<span class=\'nume\'>([0-9]*)</span>\s?(.*?)</li>')

MOVIES_RE = re.compile(r'<tr class=\'row[1-2]\'>.*?<div class=\'tit\'><a '\
              'href=\'/peliculas/([0-9]*?)/.*?/\'>(.*?)</a></div>.*?<div '\
              'class=\'font11\'>(.*?)<div class=\'reparto\'>', re.DOTALL)

MEGA_ID_RE = re.compile('goSource\((.*?)\',\'megaupload\'\)')

CAPTCHA_RE = re.compile('<img src="(http\:\/\/.*megaupload\.com\/'\
                                           'gencap.php\?.*\.gif)"')
FNAME_RE = re.compile('font-size:22px; font-weight:bold;">(.*?)</font><br>')

SOURCE_RE = re.compile("goSource\('([a-zA-Z0-9]*?)','([a-zA-Z]*?)'\)")

SEARCH_RE = re.compile('<div class=\'tit\'><a href=\'(.*?)\'>' \
                       '(.*?) \(.*\)</a></div>')

URL_OPEN = UrlOpen()  # Setup a function with cookies support


class Pycavane(object):
    """
    Provides a simple api to obtain data from cuevana
    """

    def __init__(self, username=None, password=None, cache_dir='/tmp/'):
        """
        Does the inicialization and login of the website.
        """

        Memoized.set_cache_dir(cache_dir)

        self.logged = False

        if username:
            data = {'usuario': username, 'password': password,
                    'ingresar': True, 'recordarme': 'si'}
            ret = URL_OPEN('http://www.cuevana.tv/login_get.php', data=data)
            if username not in ret:
                raise Exception('Login fail, check username and password')

            self.logged = True

    @Memoized
    def get_movies(self, letter='num', page=0):
        """
        Returns a list with (id, name, descripttion) of all the movies starting
        with `letter` or all the movies in case letter isn't set.
        """

        if not self.logged:
            raise Exception('Must be logged to retrive movies')
        all_movies = []
        while True:
            page += 1
            page_data = URL_OPEN(MOVIES_URL % (letter, page))
            moov = MOVIES_RE.findall(page_data)
            if not moov:
                break
            all_movies += moov
        return all_movies

    @Memoized
    def episodes_by_season(self, show, season_name):
        """
        Returns a list with (id, episode_number, episode_name) of
        the episodes from `show` at `seasson_name`
        """

        seasons = self.seasson_by_show(show)
        for season in seasons:
            if season[1] == season_name:
                return self.get_episodes(season)

    @Memoized
    def seasson_by_show(self, name):
        """
        Retruns a list with (id, name) of the currently avaliable
        seassons from a certain show based only on the name.
        """

        show = self.show_by_name(name)
        if show:
            return self.get_seassons(show)
        return []

    @Memoized
    def show_by_name(self, name):
        """
        Returns a tuple with (id, name) of the show
        based on the name.
        """

        for show in self.get_shows():
            if show[1] == name:
                return show

    @Memoized
    def get_shows(self, name=None):
        """
        Returns a list with (id, name) of all the
        currently avaliable shows.
        """

        series = SERIES_RE.findall(URL_OPEN(SERIES_URL))
        if name:
            series = [serie for serie in series \
                      if name.lower() in serie[1].lower()]
        return series

    @Memoized
    def get_seassons(self, serie):
        """
        Returns a list with (id, name) of the seassons of `serie`
        """

        seassons = SEASSON_RE.findall(URL_OPEN(SEASSONS_URL % serie[0]))
        return seassons

    @Memoized
    def get_episodes(self, seasson):
        """
        Returns a list with (id, episode_number, episode_name) of
        the episodes of `seasson`.
        """

        episodes = EPISODE_RE.findall(URL_OPEN(EPISODES_URL % seasson[0]))
        return episodes

    @Memoized
    def get_direct_links(self, episode, host=None, movie=False):
        """
        Returns a list with (name, link) of all avaliable host
        sources for the episode.
        """

        if movie:
            url = PLAYER_MOVIE_URL
        else:
            url = PLAYER_SEASON_URL
        data = URL_OPEN(url % episode[0])
        hosts = []
        for key, value in SOURCE_RE.findall(data):
            if not host or value == host:
                url = URL_OPEN(SOURCE_GET, data=[('key', key), ('host', value),
                       ('vars', '&id=9555&subs=,ES,EN&tipo=s&amp;sub_pre=ES')])
                # before http are ugly chars
                url = url[url.find('http:'):].split('&id')[0]

                if host:
                    return (value, url)
                hosts.append((value, url))
        return hosts

    @Memoized
    def get_subtitle(self, episode, lang='ES', filename=None, movie=False):
        """
        Downloads the subtitle of the episode.
        """

        if filename:
            filename += '.srt'
        if movie:
            url = SUB_URL_MOVIE
        else:
            url = SUB_URL_SHOW
        return URL_OPEN(url % (episode[0], lang), filename=filename)

    @Memoized
    def search_title(self, query):
        """
        Returns a list with a tuple (result_id, result_name, result_is_movie)
        with the results of the search.
        """

        result = []

        query = query.replace(" ", "+")
        page_data = URL_OPEN(SEARCH_URL % query)
        results = SEARCH_RE.findall(page_data)

        for i in results:
            url = i[0].split("/")
            result_is_movie = url[1] == "peliculas"
            result_id = url[2]
            result_name = i[1]

            result.append((result_id, result_name, result_is_movie))

        return result
