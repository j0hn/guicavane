#!/usr/bin/env python
# encoding: utf-8

"""
Player. Handles the download and starts the player.
"""

import os
import time
from megaupload import MegaFile


class Player(object):

    def __init__(self, gui, config, error_callback):
        self.gui = gui
        self.config = config
        self.pycavane = self.gui.pycavane
        self.error_callback = error_callback

    def play(self, title, is_movie=False, file_path=None, download_only=False):
        link = self.pycavane.get_direct_links(title, host="megaupload", movie=is_movie)

        if link:
            link = link[1]
        else:
            raise Exception("Not download source found")

        if file_path:
            cache_dir = file_path
        else:
            cache_dir = self.config.get_key("cache_dir")

        if is_movie:
            title = title[1]
        else:
            title = title[2]

        # Create the megaupload instance
        megafile = MegaFile(link, cache_dir, self.error_callback)
        filename = megafile.cache_file

        # Download the subtitles
        self.download_subtitles(title, filename, is_movie)

        # Start the file download
        megafile.start()

        # Wait the megaupload 45 seconds
        for i in xrange(45, 1, -1):
            loading_dots = "." * (3 - i % 4)
            self.gui.set_status_message("Please wait %d seconds%s" % (i, loading_dots))
            time.sleep(1)

        # Wait until the file exists
        file_exists = False
        while not file_exists:
            self.gui.set_status_message("A few seconds left...")
            file_exists = os.path.exists(filename)
            time.sleep(1)

        # Play or Download
        if download_only:
            self.gui.set_status_message("Downloading: %s" % title)

            # Wait till finish downloading
            while megafile.running:
                time.sleep(5)
        else:
            self.gui.set_status_message("Now playing: %s" % title)

            # Wait some more just to be sure it downloads some content
            time.sleep(5)

            player_command = self.config.get_key("player_command")
            os.system(player_command % filename)
            megafile.released = True

        # Automatic mark
        if self.config.get_key("automatic_marks"):
            self.gui.mark_selected()

    def download_subtitles(self, title, filename, is_movie):
        """
        Download the subtitle if it exists.
        """

        self.gui.set_status_message("Downloading subtitles...")
        subs_filename = filename.split(".mp4", 1)[0]

        try:
            self.pycavane.get_subtitle(title, filename=subs_filename, movie=is_movie)
        except:
            self.gui.set_status_message("Not subtitles found")
