# Base URLS
host = "http://www.monsterdivx.com"

# Shows
shows = host + "/series/"
show_info = host + '/web/series?&%s&%s&%s'
seasons = host + "/wp-content/themes/monsterdivx/scripts/getList.php?id=%s"
episodes = host + "/wp-content/themes/monsterdivx-old/scripts/getList.php?post&id=%s"
episode = host + "/%s/"

# Movies
movie_info = host + '/web/peliculas?&%s&%s'
latest_movies = host + '/peliculas/'
recomended_movies = host

# Sources
sources = host + "/wp-content/plugins/monsterdivx-player/scripts/source-iframe.php?" \
                 "monsterdivx=true&id=%s&sub=,ES&onstart=yes&sub_pre=ES"
source_get = host + "/wp-content/plugins/monsterdivx-player/scripts/source_get.php"

# Subtitles
sub_show = host + "/sub/%s_%s.srt"

# Misc
search = host + '/web/buscar?&q=%s'
