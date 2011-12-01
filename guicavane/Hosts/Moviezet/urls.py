host = 'http://www.moviezet.com/'

shows = host + 'category/shows/?page_id=2853'
movies = host + 'category/movies/'
movies_search = host + '?s=%s'

seasons = shows + '&show=%s'
episodes = seasons + '&season=%s'

episode = episodes + '&episode=%s'
movie = host + 'movies/%s'

sub_show = host + '/files/s/sub/%s_%s.srt'

thumb_url = host + '/wp-content/uploads/%s'
