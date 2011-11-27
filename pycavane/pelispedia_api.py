import re

from base_api import Episode as BaseEpisode, Show as BaseShow, \
                     Season as BaseSeason, Movie as BaseMovie
import pelispedia_urls as urls
from util import url_open, normalize_string


class Episode(object):
    _search_re =  re.compile("<option value='(?P<id>.*?)'>(?P<number>[0-9]*?)"\
                             " - (?P<name>.*?)</option>")
    _hosts_re = re.compile('var (?P<host>mega[0-9]) = "(?P<id>.*?)";')
    _host_names_re = re.compile('class="server" alt="(?P<name>.*?)"')

    def __init__(self, id, number, name):
        self.id = id
        self.__name = name
        self.number = number
        self.show = 'asd'
        self.season = 10

    @property
    def name(self):
        return self.__name

    @property
    def info(self):
        raise NotImplementedError

    @property
    def file_hosts(self):
        self.__hosts = {}

        data = url_open(self.id)
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

        return self.__hosts

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

        data = url_open(urls.episodes, {'t': season.id})
        for episode in self._search_re.finditer(data):
            yield Episode(**episode.groupdict())

    def __repr__(self):
        return '<Episode: id: "%s" number: "%s" name: "%s">' % \
                              (self.id, self.number, self.name)


class Season(BaseSeason):
    _search_re = re.compile('<option value=\'(?P<id>[0-9]*?)\'>'\
                            '(?P<name>.*?)</option>')
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def episodes(self):
        return Episode.search(self)

    @classmethod
    def search(self, show):
        data = url_open(urls.seasons, {'s': show.id})
        for season in self._search_re.finditer(data):
            yield Season(**season.groupdict())

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

class Movie(BaseMovie):
    pass
