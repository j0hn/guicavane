host = 'http://www.cuevana.tv'
static_host = 'http://sc.cuevana.tv'

movies = host + '/peliculas/lista/letra=%s&page=%s'
movie_info = host + '/peliculas/%s/%s/'
shows = host + '/web/series'
show_info = host + '/list_search_info.php?episodio=%s'
seasons = host + '/web/series?&%s&%s'
episodes = host + '/list_search_id.php?temporada=%s'

login = host + '/login_get.php'

episode = host + '/series/%s/%s/%s/'
sources = host + '/player/sources?id=%s'
player_movie = sources + '&tipo=pelicula'
player_season = sources + '&tipo=serie'
source_get = host + '/player/source_get'

sub_show = static_host + '/files/s/sub/%s_%s.srt'
sub_show_quality = static_host + '/files/s/sub/%s_%s_%s.srt'
sub_movie_quality = static_host + '/files/sub/%s_%s_%s.srt'
sub_movie = static_host + '/files/sub/%s_%s.srt'

search = host + '/web/buscar?&q=%s'
latest_movies = host + '/peliculas/'
recomended_movies = host

cuevana_url_show = host + "/series/%s/%s/%s/"
cuevana_url_movie = host + "/peliculas/%s/%s/"
