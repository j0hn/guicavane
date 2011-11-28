host = 'http://www.moviezet.com/'

shows = host + 'category/shows/?page_id=2853'
seasons = shows + '&show=%s'
episodes = seasons + '&season=%s'

episode = episodes + '&episode=%s'

sub_show = host + '/files/s/sub/%s_%s.srt'
