import re

from util import UrlOpen
from memo import Memoized

host = 'http://www.cuevana.tv'

movies_url = host+'/peliculas/lista/letra=%s&page=%s'
series_url = host+'/series/'
seassons_url = host+'/list_search_id.php?serie=%s'
episodes_url = host+'/list_search_id.php?temporada=%s'

episode_url = host+"/series/%s/%s/%s/"
player_movie_url = host+'/player/source?id=%s'
player_season_url = player_movie_url+'&tipo=s'
source_get = host+'/player/source_get'

sub_url_movie = host+'/files/sub/%s_%s.srt'
sub_url_show = host+'/files/s/sub/%s_%s.srt'


series_re = re.compile('serieslist.push\(\{id:([0-9]*),nombre:"(.*?)"\}\);')
seasson_re = re.compile('<li onclick=\'listSeries\(2,"([0-9]*)"\)\'>(.*?)</li>')
episode_re = re.compile('<li onclick=\'listSeries\(3,"([0-9]*)"\)\'>'\
                        '<span class=\'nume\'>([0-9]*)</span>\s?(.*?)</li>')

movies_re = re.compile(r'<tr class=\'row[1-2]\'>.*?<div class=\'tit\'><a '\
              'href=\'/peliculas/([0-9]*?)/.*?/\'>(.*?)</a></div>.*?<div '\
              'class=\'font11\'>(.*?)<div class=\'reparto\'>', re.DOTALL)

mega_id_re = re.compile('goSource\((.*?)\',\'megaupload\'\)')

captcha_re = re.compile('<img src="(http\:\/\/.*megaupload\.com\/'\
                                           'gencap.php\?.*\.gif)"')
fname_re = re.compile('font-size:22px; font-weight:bold;">(.*?)</font><br>')

source_re = re.compile("goSource\('([a-zA-Z0-9]*?)','([a-zA-Z]*?)'\)")

# Setup a function with cookies support
url_open = UrlOpen()


class Pycavane(object):
    def __init__(self, username=None, password=None,
                      cache_dir='/tmp/', lifetime=20):
        Memoized.set_cache_dir(cache_dir)

        self.logged = False

        if username:
            data = {'usuario': username, 'password': password,
                            'ingresar': True, 'reordame': 'si'}
            ret = url_open('http://www.cuevana.tv/login_get.php', data=data)
            if username not in ret:
                raise Exception, 'Login fail, check username and password'

            self.logged = True

    @Memoized
    def get_movies(self, letter='num', page=0):
        if not self.logged:
            raise Exception, 'Must be logged to retrive movies'
        all_movies = []
        while True:
            page += 1
            page_data = url_open(movies_url%(letter, page))
            moov = movies_re.findall(page_data)
            if not moov:
                break
            all_movies += moov
        return all_movies

    @Memoized
    def episodes_by_season(self, show, season_name):
        seasons = self.seasson_by_show(show)
        for season in seasons:
            if season[1] == season_name:
                return self.get_episodes(season)

    @Memoized
    def seasson_by_show(self, name):
        show = self.show_by_name(name)
        if show:
            return self.get_seassons(show)
        return []

    @Memoized
    def show_by_name(self, name):
        for show in self.get_shows():
            if show[1] == name:
                return show

    @Memoized
    def get_shows(self, name=None):
        series = series_re.findall(url_open(series_url))
        if name:
            series = [serie for serie in series \
                       if name.lower() in serie[1].lower()]
        return series

    @Memoized
    def get_seassons(self, serie):
        seassons = seasson_re.findall(url_open(seassons_url % serie[0]))
        return seassons

    @Memoized
    def get_episodes(self, seasson):
        episodes = episode_re.findall(url_open(episodes_url % seasson[0]))
        return episodes

    @Memoized
    def get_direct_links(self, episode, host=None, movie=False):
        if movie:
            url = player_movie_url
        else:
            url = player_season_url
        data = url_open(url % episode[0])
        hosts = []
        for key, value in source_re.findall(data):
            if not host or value == host:
                url = url_open(source_get, data=[('key', key), ('host', value),
                       ('vars', '&id=9555&subs=,ES,EN&tipo=s&amp;sub_pre=ES')])
                # before http are ugly chars
                url = url[url.find('http:'):].split('&id')[0]

                if host:
                    return (value, url)
                hosts.append((value, url))
        return hosts

    @Memoized
    def get_subtitle(self, episode, lang='ES', filename=None, movie=False):
        if filename:
            filename += '.srt'
        if movie:
            url = sub_url_movie
        else:
            url = sub_url_show
        return url_open(url % (episode[0], lang), filename=filename)
