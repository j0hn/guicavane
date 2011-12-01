# Base URLS
host = 'http://www.cuevana.tv'
static_host = 'http://sc.cuevana.tv'

# Shows
shows = host + '/web/series?&todas'
show_info = host + '/web/series?&%s&%s&%s'
seasons = host + '/web/series?&%s&%s'

# Movies
movie_info = host + '/web/peliculas?&%s&%s'
latest_movies = host + '/peliculas/'
recomended_movies = host

# Sources
sources = host + '/player/sources?id=%s'
movie_sources = sources + '&tipo=pelicula'
show_sources = sources + '&tipo=serie'
source_get = host + '/player/source_get'

# Subtitles
sub_show = static_host + '/files/s/sub/%s_%s.srt'
sub_show_quality = static_host + '/files/s/sub/%s_%s_%s.srt'
sub_movie = static_host + '/files/sub/%s_%s.srt'
sub_movie_quality = static_host + '/files/sub/%s_%s_%s.srt'

# Misc
search = host + '/web/buscar?&q=%s'
