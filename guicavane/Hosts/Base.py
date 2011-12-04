#!/usr/bin/env python
# coding: utf-8

"""
Host Base API.

To implement a new site just follow this API.
"""


class BaseResource(object):
    def get_subtitle_url(self, lang="ES", quality=None):
        """ Returns the url of this episode's subtitle. """

        raise NotImplementedError

    @property
    def file_hosts(self):
        """ Returns a a dict with {name: {quality: url}} of all the avaliable
        download hosts for this episode.

        Example:
            {
             'megaupload':
                {'360': 'http://www.megauplo...',
                 '720': 'http://www.megauplo...'
                },
             'bitshare':
                {'360': 'http://www.bitshare...'}
            }
        """

        raise NotImplementedError

    @property
    def original_url(self):
        """ Returns the link to this episode on the original webpage. """

        raise NotImplementedError


class BaseEpisode(BaseResource):
    def __init__(self, id, name, number, season, show, *args):
        """ Creates an episode with an id, number and name.
        season and show are references to it's episode Season
        and Show objects.
        Extra arguments can be given. """

        raise NotImplementedError

    @property
    def info(self):
        """ Returns a dict with the episode's info. The dict should have
        the following keys:
            * image: (string) url of the episode's cover.
            * description: (string) just a brief description of the episode
            * cast: (list)
            * genere: (string)
            * language: (string)
        """

        raise NotImplementedError

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class BaseSeason(object):
    def __init__(self, id, name, number, show, *args):
        """ Creates a Season with an id and name.
        show is a reference to this season's show.
        Extra arguments can be given. """

        raise NotImplementedError

    @property
    def episodes(self):
        """ Returns a generator with all the episodes
        from this season. """

        raise NotImplementedError

    @property
    def info(self):
        # TODO: define this info items
        raise NotImplementedError

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)


class BaseShow(object):
    def __init__(self, id, name, *args):
        """ Creates a show with an id and name.
        Extra arguments can be given """

        raise NotImplementedError

    @property
    def seasons(self):
        """ Returns a generator with all the seasons for
        this show. """

        raise NotImplementedError

    @property
    def info(self):
        # TODO: define this info items
        raise NotImplementedError

    @classmethod
    def search(cls, name=""):
        """ Returns a generator with all the currently avaliable Shows.
        If name is given, the shows returned match with name. """

        raise NotImplementedError

    def __repr__(self):
        return '<Show: id: "%s" name: "%s">' % (self.id, self.name)


class BaseMovie(BaseResource):
    def __init__(self, id, name, *args):
        """ Creates a movie with an id and name.
        Extra arguments can be given """

        raise NotImplementedError

    @property
    def info(self):
        """ Returns a dict with info about this movie.
        The dict has the following keys:
            * descripion: (string)
            * year: (int)
            * cast: (list)
            * language: (string)
            * duration: (int) in minutes
            * director: (string)
            * genere: (string)
        """

        raise NotImplementedError

    @classmethod
    def search(cls, query=""):
        """ Returns a generator with all the matched
        Movies searched using the query. """

        raise NotImplementedError

    @classmethod
    def get_latest(cls):
        """ Returns a generator with all the latest movies. """

        raise NotImplementedError

    @classmethod
    def get_recomended(cls):
        """ Returns a generator with all the recomended movies. """

        raise NotImplementedError

    def __repr__(self):
        return '<Movie id: "%s" name: "%s">' % (self.id, self.name)
