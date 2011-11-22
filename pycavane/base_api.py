#!/usr/bin/env python
# coding: utf-8

"""
Pycavane

A library to scrap the website www.cuevana.tv
Author: Roger Duran <rogerduran@gmail.com>
Contributor: j0hn <j0hn.com.ar@gmail.com>
"""


class Episode(object):
    def __init__(self, id, number, name):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    @property
    def info(self):
        raise NotImplementedError

    @property
    def file_hosts(self):
        raise NotImplementedError

    def get_subtitle(self, lang='ES', filename=None):
        raise NotImplementedError

    @classmethod
    def search(self, season):
        """
        Returns a list with Episodes of
        of `season`.
        """
        raise NotImplementedError

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(object):
    def __init__(self, id, name):
        raise NotImplementedError

    @property
    def episodes(self):
        raise NotImplementedError

    @classmethod
    def search(self, show):
        raise NotImplementedError

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)


class Show(object):
    def __init__(self, id, name):
        raise NotImplementedError

    @property
    def seasons(self):
        """
        Returns a list with Seasons
        """
        return Season.search(self)

    @property
    def description(self):
        raise NotImplementedError

    @classmethod
    def search(self, name=''):
        """
        Returns a list with all the
        currently avaliable Shows
        """
        raise NotImplementedError

    def __repr__(self):
        return '<Show: id: "%s" name: "%s">' % (self.id, self.name)


class Movie(object):
    def __init__(self, id, name, year=None, description=""):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    @property
    def info(self):
        """
        Returns a dict with info about this movie
        """
        raise NotImplementedError


    @classmethod
    def search(self, query=""):
        """
        Returns a list with all the matched
        movies searched using the query
        """
        raise NotImplementedError

    def __repr__(self):
        return '<Movie id: "%s" name: "%s">' % (self.id, self.name)
