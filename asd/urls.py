host = 'http://www.cuevana.tv'

movies = host + '/peliculas/lista/letra=%s&page=%s'
movie_info = host + '/peliculas/%s/%s/'
shows = host + '/series/'
show_info = host + '/list_search_info.php?episodio=%s'
seasons = host + '/list_search_id.php?serie=%s'
episodes = host + '/list_search_id.php?temporada=%s'

login = host + '/login_get.php'

episode = host + '/series/%s/%s/%s/'
player_movie = host + '/player/source?id=%s'
player_season = player_movie + '&tipo=s'
source_get = host + '/player/source_get'

sub_show = host + '/download_sub?file=s/sub/%s_%s.srt'
sub_movie = host + '/download_sub?file=sub/%s_%s.srt'

search = host + '/buscar/?q=%s&cat=titulo'
