#!/usr/bin/env python
# coding: utf-8

"""
Freevana api

Author: j0hn <j0hn.com.ar@gmail.com>
"""

import os
import sqlite3

import urls
from util import url_open
from base_api import Episode as BaseEpisode, \
                     Show as BaseShow, \
                     Season as BaseSeason, \
                     Movie as BaseMovie


# Download latest freevana database from: http://tirino.github.com/freevana/
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = "freevana.db"
DB_CONN = sqlite3.connect(os.path.join(BASE_PATH, DATABASE_FILE),
                          check_same_thread=False)


class Episode(object):
    _query_all = "SELECT id, name, number FROM series_episodes " \
                 "WHERE season_id = '%s'"
    _query_sources = "SELECT source, url FROM series_episode_sources " \
                     "WHERE definition = '360' AND series_episode_id = '%s'"

    def __init__(self, id, name, number, show_name, season_name):
        self.id = id
        self.__name = name
        self.number = number
        self.show = show_name
        self.season = int(season_name.replace("Temporada ", ""))

    @property
    def name(self):
        return self.__name

    @property
    def info(self):
        raise NotImplementedError

    @property
    def file_hosts(self):
        hosts = {}

        cur = DB_CONN.cursor()

        hostmap = {'megaupload': 'http://www.megaupload.com/?d=',
                   'bitshare': 'http://bitshare.com/?f=',
                   'filefactory': 'http://www.filefactory.com/file/'
                   }

        result = cur.execute(self._query_sources % self.id)
        for row in result:
            hosts[row[0]] = row[1]

        return hosts


    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        try:
            result = url_open(urls.sub_show % (self.id, lang), filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    @classmethod
    def search(self, season):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_all % season.id)

        for row in result:
            show_name = season.show
            season_name = season.name

            row = list(row) + [show_name, season_name]
            yield Episode(*row)

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(BaseSeason):
    _query_all = "SELECT id, name FROM series_seasons " \
                 "WHERE series_id = '%s' ORDER BY number ASC"

    def __init__(self, id, name, show_name):
        self.id = id
        self.name = name
        self.show = show_name

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_all % show.id)

        for row in result:
            row = list(row) + [show.name]
            yield Season(*row)

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)

class Show(BaseShow):
    _query_all = "SELECT id, name FROM series ORDER BY name ASC"
    _query_one = "SELECT id, name FROM series WHERE name = '%s'"

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        return Season.search(self)

    @property
    def description(self):
        raise NotImplementedError

    @classmethod
    def search(self, name=''):
        cur = DB_CONN.cursor()

        if name:
            result = cur.execute(self._query_one % name)
        else:
            result = cur.execute(self._query_all)

        for row in result:
            yield Show(*row)

    def __repr__(self):
        return '<Show: id: "%s" name: "%s">' % (self.id, self.name)

class Movie(BaseMovie):
    _query_search = "SELECT id, name FROM movies WHERE name LIKE '%%%s%%'"
    _query_sources = "SELECT source, url FROM movie_sources " \
                     "WHERE definition = '360' AND movie_id = '%s'"
    def __init__(self, id, name, year=None, description=""):
        self.id = id
        self.name = name

    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        try:
            result = url_open(urls.sub_movie % (self.id, lang), filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    @property
    def file_hosts(self):
        hosts = {}

        cur = DB_CONN.cursor()

        hostmap = {'megaupload': 'http://www.megaupload.com/?d=',
                   'bitshare': 'http://bitshare.com/?f=',
                   'filefactory': 'http://www.filefactory.com/file/'
                   }

        result = cur.execute(self._query_sources % self.id)
        for row in result:
            hosts[row[0]] = row[1]

        return hosts

    @classmethod
    def search(self, query=""):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_search % query)

        for row in result:
            yield Movie(row[0], row[1])
