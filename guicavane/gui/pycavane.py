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
SHOWS_URL = HOST + '/series/'
SHOW_INFO_URL = HOST + '/list_search_info.php?episodio=%s'
SEASSONS_URL = HOST + '/list_search_id.php?serie=%s'
EPISODES_URL = HOST + '/list_search_id.php?temporada=%s'

EPISODE_URL = HOST + '/series/%s/%s/%s/'
PLAYER_MOVIE_URL = HOST + '/player/source?id=%s'
PLAYER_SEASON_URL = PLAYER_MOVIE_URL + '&tipo=s'
SOURCE_GET = HOST + '/player/source_get'

SUB_URL_MOVIE = HOST + '/files/sub/%s_%s.srt'
SUB_URL_SHOW = HOST + '/files/s/sub/%s_%s.srt'
SUB_URL_SHOW = HOST + '/download_sub?file=s/sub/%s_%s.srt'
SUB_URL_MOVIE = HOST + '/download_sub?file=sub/%s_%s.srt'

SEARCH_URL = HOST + '/buscar/?q=%s&cat=titulo'

SHOWS_RE = re.compile('serieslist.push\(\{id:([0-9]*),nombre:"(.*?)"\}\);')
SEASSON_RE = re.compile('<li onclick=\'listSeries\(2,"([0-9]*)"\)\'>(.*?)</li>')
EPISODE_RE = re.compile('<li onclick=\'listSeries\(3,"([0-9]*)"\)\'>'\
                        '<span class=\'nume\'>(.*?)</span>\s?(.*?)</li>')

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

MAYBE_MEANT = re.compile("Quizás quiso decir: <a href='.*?'>(.*?)</a>")

SHOW_INFO_IMAGE_RE = re.compile('<img src="(.*?)" border="0" />')
SHOW_INFO_DESCRIPTION_RE = re.compile('<div>(.*)<div class="sep"></div>', re.DOTALL)
SHOW_INFO_CAST_RE = re.compile('<a href=\'/buscar/\?q=.*?&cat=actor\'>(.*?)</a>')
SHOW_INFO_GENERE_RE = re.compile('<b>Género:</b>(.*?)<br />')
SHOW_INFO_LANGUAGE_RE = re.compile('<b>Idioma:</b>(.*?)<br />')

# Favorites support
FAVORITES_URL = HOST + '/user_fav.php'
ADD_FAVORITES_URL = HOST + '/botlink_fav.php?id=%s&serie=%s'

FAVORITE_SERIES_RE = re.compile('<a href=\'/series/[0-9]*/[^/]*/\'>([^<]*)</a>')
FAVORITE_MOVIES_RE = re.compile('<a href=\'/peliculas/[0-9]*/[^/]*/\'>([^<]*)</a>')

URL_OPEN = UrlOpen()  # Setup a function with cookies support


class Pycavane(object):
    """
    Provides a simple api to obtain data from cuevana
    """

    def __init__(self, cache_dir='/tmp/', cache_lifetime=60*60*6):
        """
        Does the inicialization and login of the website.
        """

        Memoized.set_cache_dir(cache_dir)
        Memoized.set_lifetime(cache_lifetime)

        self.logged = False

    def login(username=None, password=None):
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

    def movie_by_name(self, name):
        """
        Returns a tuple with (id, name) of the movie
        based on the name.
        """

        movies = self.search_title(name)[0]
        found = False
        for movie in movies:
            if movie[1] == name:
                found = movie
                break

        assert found != False

        return (movie[0], movie[1])


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
    def episode_by_name(self, name, show, seasson):
        episode_found = None

        for episode in self.episodes_by_season(show, seasson):
            if episode[2] == name:
                episode_found = episode
                break

        return episode_found

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

        series = SHOWS_RE.findall(URL_OPEN(SHOWS_URL))
        if name:
            series = [serie for serie in series \
                      if name.lower() in serie[1].lower()]
        return series

    @Memoized
    def get_episode_info(self, episode):
        """
        Returns a tuple with (image, episode_name, description,
        cast, genere, language) of the show with the given episode.
        """

        page_data = URL_OPEN(SHOW_INFO_URL % episode[0])

        name = episode[2]
        image = HOST + SHOW_INFO_IMAGE_RE.findall(page_data)[0]
        desc = SHOW_INFO_DESCRIPTION_RE.findall(page_data)[0].strip()
        cast = SHOW_INFO_CAST_RE.findall(page_data)
        genere = SHOW_INFO_GENERE_RE.findall(page_data)[0].strip()
        language = SHOW_INFO_LANGUAGE_RE.findall(page_data)[0].strip()

        return (image, name, desc, cast, genere, language)

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

        search_list = []

        query = query.replace(" ", "+")
        page_data = URL_OPEN(SEARCH_URL % query)
        results = SEARCH_RE.findall(page_data)
        maybe_meant = MAYBE_MEANT.findall(page_data)
        if maybe_meant:
            maybe_meant = maybe_meant[0]

        for i in results:
            url = i[0].split("/")
            result_is_movie = url[1] == "peliculas"
            result_id = url[2]
            result_name = i[1]

            search_list.append((result_id, result_name, result_is_movie))

        result = (search_list, maybe_meant)

        return result

    def get_favorite_series(self):
        if not self.logged:
            return []
        rc = URL_OPEN(FAVORITES_URL, data={'tipo': 'serie'})
        return FAVORITE_SERIES_RE.findall(URL_OPEN(FAVORITES_URL,
                                                   data={'tipo': 'serie'}))

    def get_favorite_movies(self):
        if not self.logged:
            return []

        return FAVORITE_MOVIES_RE.findall(URL_OPEN(FAVORITES_URL,
                                                   data={'tipo': 'pelicula'}))

    def add_favorite(self, name, is_movie):
        if is_movie:
            idnum, _ = self.movie_by_name(name)
            URL_OPEN(ADD_FAVORITES_URL % (idnum, 'false'))
        else:
            idnum, _ = self.show_by_name(name)
            URL_OPEN(ADD_FAVORITES_URL % (idnum, 'true'))

    def del_favorite(self, name, is_movie):
        if is_movie:
            idnum, _ = self.movie_by_name(name)
            URL_OPEN(FAVORITES_URL,
                     data={'tipo':'pelicula', 'eliminar':'true', 'id': idnum})
        else:
            idnum, _ = self.show_by_name(name)
            URL_OPEN(FAVORITES_URL,
                     data={'tipo':'serie', 'eliminar':'true', 'id': idnum})
