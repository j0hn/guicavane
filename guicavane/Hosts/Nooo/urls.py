# Base URLS
host = 'http://nooo.tv'

# Shows

# Movies
latest_movies = host + '/web/peliculas?&recientes'

# Sources
sources = host + '/player/sources?id=%s'
movie_sources = sources + '&tipo=pelicula'
show_sources = sources + '&tipo=serie'
source_get = host + '/player/source_get'

# Subtitles

# Misc
search = host + '?s=+%s&submitButton='
