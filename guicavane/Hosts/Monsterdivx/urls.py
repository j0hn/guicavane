# Base URLS
host = "http://www.monsterdivx.com"

# Shows
shows = host + "/series/"
seasons = host + "/wp-content/themes/monsterdivx/scripts/getList.php?id=%s"
episodes = host + "/wp-content/themes/monsterdivx-old/scripts/getList.php?post&id=%s"
episode = host + "/%s/"

# Movies

# Sources
sources = host + "/wp-content/plugins/monsterdivx-player/scripts/source-iframe.php?" \
                 "monsterdivx=true&mid=%s&sub=,ES&sub_pre=ES"
source_get = host + "/wp-content/plugins/monsterdivx-player/scripts/source_get.php"

# Subtitles
sub_show = host + "/sub/%s_%s.srt"

# Misc
search = host + "/wp-content/themes/monsterdivx/scripts/suggest.php"
