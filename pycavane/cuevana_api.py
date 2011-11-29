#!/usr/bin/env python
# coding: utf-8

"""
Pycavane

A library to scrap the website www.cuevana.tv
Author: Roger Duran <rogerduran@gmail.com>
Contributor: j0hn <j0hn.com.ar@gmail.com>
"""

import re
import json

import cuevana_urls as urls
from util import url_open, normalize_string
from cached import Cached


def setup(username=None, password=None,
        cache_dir='/tmp/', cache_lifetime=60*60*6):
    """ Does the inicialization and login of the website. """

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
    _sources_re = re.compile('sources = ({.*?}), sel_source')
    _image_re = re.compile('<div class="img"><img src="(.*?)" /></div>')
    _description_re = re.compile('<h2>Sinopsis</h2>(.*?)<div class="sep">', re.DOTALL)
    _cast_re = re.compile("<a href='#!/buscar/actor:.*?'>(.*?)</a>")
    _genere_re = re.compile('<b>Género:</b>(.*?)</div>')
    _language_re = re.compile('<b>Idioma:</b>(.*)</div>')

    __info = None
    __hosts = None
    __name = ''

    def __init__(self, id, number, name, url, season):
        self.id = id
        self.number = number
        self.name = name
        self.url = url
        self.season = season.number
        self.show = season.show.name
        self.show_obj = season.show
        self.urlname = self.url.rsplit("/")[-1]

        info_keys = ['image', 'description', 'cast', 'genere',
                     'language']

        for info_key in info_keys:
            setattr(self.__class__, info_key,
                    property(lambda self, i=info_key:self.info[i]))

    def get_subtitle(self, lang='ES', quality=None, filename=None):
        """ Downloads the subtitle of the episode. """

        if filename:
            filename += '.srt'

        if quality:
            url = urls.sub_show_quality % (self.id, lang, quality)
        else:
            url = urls.sub_show % (self.id, lang)

        try:
            result = url_open(url, filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    @property
    def info(self):
        """ set info data in __info dict and return it. """

        if self.__info:
            return self.__info

        page_data = url_open(urls.show_info % \
            (self.id, self.show_obj.urlname, self.urlname))

        image = self._image_re.search(page_data).group(1)
        description = self._description_re.search(page_data).group(1).strip()
        cast = self._cast_re.findall(page_data)
        genere = self._genere_re.search(page_data).group(1).strip()
        language = self._language_re.search(page_data).group(1).strip()

        self.__info = {'image': image, 'description': description,
                'cast': cast, 'genere': genere, 'language': language,
                'name': self.name, 'season': self.season}

        return self.__info

    @property
    def file_hosts(self):
        """ Returns a a dict with name and instance. """

        if self.__hosts:
            return self.__hosts
        self.__hosts = {}

        data = url_open(urls.player_season % self.id)
        sources = json.loads(self._sources_re.search(data).group(1))

        for host in sources["360"]["2"]:

            data = [("id", self.id), ("tipo", "serie"),
                    ("def", "360"), ("audio", "2"),
                    ("host", host)]

            hostdata = url_open(urls.source_get, data=data)

            # before http are ugly chars
            url = hostdata[hostdata.find('http:'):].split('&id')[0]

            self.__hosts[host] = url

        return self.__hosts

    @property
    def cuevana_url(self):
        """ Returns the link to this episode on cuevana. """

        name = self.normalized_name
        show = normalize_string(self.show)
        return urls.cuevana_url_show % (self.id, show, name)

    @property
    def normalized_name(self):
        return normalize_string(self.info["name"])


    @classmethod
    def search(self, season):
        raise NotImplementedError()

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(object):
    _json_re = re.compile("serieList\({l:({.*?}),e", re.DOTALL)

    def __init__(self, number, episodes, show):
        self.id = number
        self.number = number
        self.name = "Temporada %s" % number
        self._episodes = episodes
        self.show = show

    @property
    def episodes(self):
        for ep in self._episodes:
            yield Episode(ep["id"], ep["num"], ep["tit"], ep["url"], self)

    @classmethod
    def search(self, show):
        """ Returs a list with the seasons from show. """

        data = url_open(urls.seasons % (show.id, show.urlname))
        jsondata = json.loads(self._json_re.search(data).group(1))

        for data in jsondata:
            yield Season(data, jsondata[data], show)

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)


class Show(object):
    _json_re = re.compile("c.listSerie\('',(.*?)\);", re.DOTALL)

    def __init__(self, url, name):
        url = url.split("/")

        self.id = url[2]
        self.urlname = url[3]
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

        data = url_open(urls.shows)
        jsondata = json.loads(self._json_re.search(data).group(1))

        for show in jsondata:
            if not name or name in show['tit'].lower():
                yield Show(show["url"], show["tit"])

    def __unicode__(self):
        return u'<Show: id: "%s" name: "%s">' % (self.id, self.name)

    def __repr__(self):
        return repr(unicode(self))


class Movie(object):
    _search_re = re.compile('<div class=\'tit\'>' \
                            '<a href=\'/peliculas/(?P<id>[0-9]*)/.*?\'>' \
                            '(?P<name>.*?) \((?P<year>[0-9]*)\)</a>' \
                            '</div>.*?<div class=\'txt\'>' \
                            '(?P<description>.*?)<div', re.DOTALL)
    _latest_re = re.compile('<div class=\'tit\'>' \
                            '<a href=\'/peliculas/(?P<id>[0-9]*)/.*?\'>' \
                            '(?P<name>.*?)</a>.*?' \
                            '<div class=\'font11\'>(?P<description>.*?)' \
                            '<div class=\'reparto\'>', re.DOTALL)
    _recomended_re = re.compile('loadedinfo\["d(?P<id>[0-9]*)"\]' \
                                '.*?tit: "(?P<name>.*?)\(', re.DOTALL)
    _name_re = re.compile( r'<div class="tit">(.*?)</div>')
    _image_re = re.compile('<div class="headimg"><img src="(.*?)"')
    _description_re = re.compile('<td class="infolabel" valign="top">Sinopsis</td>.*?' \
                                 '<td>(.+?)</td>', re.DOTALL)
    _cast_re = re.compile('<a href=\'/buscar/\?q=.*?&cat=actor\'>(.*?)</a>')
    _genere_re = re.compile('<b>Género:</b>(.*?)<br />')
    _language_re = re.compile('<b>Idioma:</b>(.*?)<br />')
    _hosts_re = re.compile("goSource\('([a-zA-Z0-9]*?)','([a-zA-Z]*?)'\)")

    #############

    _search_re = re.compile("\$\('#list'\).list\({l:(.*?), set:\[")
    _sources_re = re.compile('sources = ({.*?}), sel_source')

    __info = ""
    __hosts = None

    def __init__(self, id, name, year=None, description=""):
        self.id = id
        self.name = name
        self.year = year
        self.__description = description

    def get_subtitle(self, lang='ES', quality=None, filename=None):
        """ Downloads the subtitle of the movie. """

        if filename:
            filename += '.srt'

        if quality:
            url = urls.sub_movie_quality % (self.id, lang, quality)
        else:
            url = urls.sub_movie % (self.id, lang)

        try:
            result = url_open(url, filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    @property
    def description(self):
        if self.__description.endswith('...'):
            return self.info['description']

        return self.__description

    @property
    def cuevana_url(self):
        """ Returns the link to this episode on cuevana. """

        name = self.normalized_name
        return urls.cuevana_url_movie % (self.id, name)

    @property
    def normalized_name(self):
        return normalize_string(self.name)

    @property
    def info(self):
        """ Returns a dict with info about this movie. """

        if self.__info:
            return self.__info

        page_data = url_open(urls.movie_info % (self.id, self.normalized_name))

        name = self._name_re.findall(page_data)[0].strip()
        image = self._image_re.findall(page_data)[0]
        description = self._description_re.findall(page_data)[0].strip()
        cast = self._cast_re.findall(page_data)
        genere = self._genere_re.findall(page_data)[0].strip()
        language = self._language_re.findall(page_data)[0].strip()

        self.__info = {'name': name, 'image': image, 'description': description,
                'cast': cast, 'genere': genere, 'language': language}

        return self.__info

    @property
    def file_hosts(self):
        """ Returns a a dict with name and instance. """

        if self.__hosts:
            return self.__hosts
        self.__hosts = {}

        data = url_open(urls.player_movie % self.id)
        sources = json.loads(self._sources_re.search(data).group(1))

        for host in sources["360"]["2"]:

            data = [("id", self.id), ("tipo", "pelicula"),
                    ("def", "360"), ("audio", "2"),
                    ("host", host)]

            hostdata = url_open(urls.source_get, data=data)

            # before http are ugly chars
            url = hostdata[hostdata.find('http:'):].split('&id')[0]

            self.__hosts[host] = url

        return self.__hosts

    @classmethod
    def search(self, query=""):
        """ Returns a list with all the matched
        movies searched using the query. """

        query = query.lower().replace(' ', '+')

        data = url_open(urls.search % query)
        data = json.loads(self._search_re.search(data).group(1))

        for movie in data:
            if not "#!/peliculas" in movie["url"]:
                continue

            yield Movie(movie["id"], movie["tit"])

    @classmethod
    def get_latest(self):
        """ Returns a list with all the latest
        movies. """

        data = url_open(urls.latest_movies)
        for movie in self._latest_re.finditer(data):
            movie_dict = movie.groupdict()
            movie_dict['description'] = movie_dict['description'].strip()

            yield Movie(**movie_dict)

    @classmethod
    def get_recomended(self):
        """ Returns a list with all the recomended
        movies. """

        data = url_open(urls.recomended_movies)
        data = data.split("<h3>Películas destacadas</h3>")[1].split("<h3>Episodios destacados</h3>")[0]
        for movie in self._recomended_re.finditer(data):
            movie_dict = movie.groupdict()
            movie_dict["name"] = movie_dict["name"].strip()

            yield Movie(**movie_dict)

    def __repr__(self):
        return '<Movie id: "%s" name: "%s">' % (self.id, self.name)
