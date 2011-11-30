import re

from base_api import Episode as BaseEpisode, Show as BaseShow, \
                     Season as BaseSeason, Movie as BaseMovie
import pelispedia_urls as urls
from util import url_open

HOSTMAP = {'megaupload': 'http://www.megaupload.com/?d=',
           'kickupload': 'http://www.kickupload.com/files/',
           'bitshare': 'http://bitshare.com/?f=',
           'filefactory': 'http://www.filefactory.com/file/',
           'hotfile': 'http://hotfile.com/dl/',
           }

HOSTNAMES = {'mega1': 'megaupload',
            'mega2': 'bitshare',
            'mega3': 'filefactory',
            'mega4': 'hotfile',
            'mega5': 'wupload',
            'mega6': 'glumbo',
            'mega7': 'uploadhere',
            'mega8': 'uploadking',
            }

class Hosts(object):
    __hosts = None

    @property
    def file_hosts(self):
        if self.__hosts:
            return self.__hosts
        self.__hosts = {}

        data = url_open(self.id)
        for name, _id in self._hosts_re.findall(data):
            if not _id:
                continue
            hostname = HOSTNAMES[name]
            if hostname not in HOSTMAP:
                print hostname, "not implemented"
                continue
            self.__hosts[hostname] = HOSTMAP[hostname] + _id
        return self.__hosts


class Episode(Hosts, BaseEpisode):
    _search_re =  re.compile("<option value='(?P<id>.*?)'>(?P<number>[0-9]*?)"\
                             " - (?P<name>.*?)</option>")
    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')

    def __init__(self, id, number, name, show, season):
        self.id = id
        self.__name = name
        self.number = number
        self.show = show
        self.season = season

    @property
    def name(self):
        return self.__name

    @property
    def info(self):
        raise NotImplementedError

    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        id = self.id.split('/play/')[1].split('/', 1)[0]

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

        data = url_open(urls.episodes, {'ss': season.show_id,
                                        't': season.id})
        for episode in self._search_re.finditer(data):
            episode_dict = episode.groupdict()
            episode_dict["show"] = season.show
            episode_dict["season"] = season.id
            yield Episode(**episode_dict)

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(BaseSeason):
    _search_re = re.compile('<option value=\'(?P<id>[0-9]*?)\'>'\
                            '(?P<name>.*?)</option>')
    def __init__(self, id, name, show, show_id):
        self.id = id
        self.name = name
        self.show = show
        self.show_id = show_id

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        data = url_open(urls.seasons, {'s': show.id})
        for season in self._search_re.finditer(data):
            season_dict = season.groupdict()
            season_dict["show"] = show.name
            season_dict["show_id"] = show.id
            yield Season(**season_dict)

    def __repr__(self):
        return '<Season: id: "%s" name: "%s">' % (self.id, self.name)

class Show(BaseShow):
    _search_re = re.compile('<option value="(?P<id>[0-9]*?)">'\
                            '(?P<name>.*?)</option>')
    def __init__(self, id, name):
        self.id = id
        self.name = name

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

        name = name.lower()

        data = url_open(urls.shows)
        data = data.split('<select name="s" id="serie" size="15">')[1]
        data = data.split('</select>', 1)[0]

        for show in self._search_re.finditer(data):
            show_dict = show.groupdict()
            if not name or name in show_dict['name'].lower():
                yield Show(**show_dict)

    def __repr__(self):
        return '<Show: id: "%s" name: "%s">' % (self.id, self.name)

class Movie(BaseMovie, Hosts):
    _search_re = re.compile('<div class="titletip"><b><a '\
            'href="(?P<id>http://www.pelispedia.com/movies/play/'\
            '.*?)">(?P<name>.*?)</a></b></div>')
    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')
    _host_names_re = re.compile('class="server" alt="(?P<name>.*?)"')
    def __init__(self, id, name, year=None, description=""):
        self.id = id
        self.name = name
        self.year = year
        self.__description = description

    @classmethod
    def search(self, query=""):
        """ Returns a list with all the matched
        movies searched using the query. """

        query = query.lower().replace(' ', '+')

        data = url_open(urls.movies % query)

        for movie in self._search_re.finditer(data):
            movie_dict = movie.groupdict()
            yield Movie(**movie_dict)

    def get_subtitle(self, lang='ES', filename=None):
        if filename:
            filename += '.srt'

        id1, id2 = self.id.split('/play/')[1].split('/', 1)[0].split("-")
        id = "%s-%s" % (id2, id1)

        try:
            result = url_open(urls.sub_movie % id, filename=filename)
        except:
            raise Exception("Subtitle not found")

        return result

    def __repr__(self):
        return '<Movie id: "%s" name: "%s">' % (self.id, self.name)
