#!/usr/bin/env python
# encoding: utf-8

"""
Player. Handles the download and starts the player.
"""

import os
import time
import gobject
import subprocess
from megaupload import MegaFile


class Player(object):
    """
    Class that takes care of the downloading and correctly
    playing the file.
    """

    def __init__(self, gui, config, error_callback):
        self.gui = gui
        self.config = config
        self.pycavane = self.gui.pycavane
        self.error_callback = error_callback

    def play(self, to_download, is_movie=False,
             file_path=None, download_only=False):
        """
        Starts the playing of `to_download`.
        """

        link = self.pycavane.get_direct_links(to_download, host="megaupload",
                                              movie=is_movie)

        if link:
            link = link[1]
        else:
            raise Exception("Not download source found")

        if file_path:
            cache_dir = file_path
        else:
            cache_dir = self.config.get_key("cache_dir")

        if is_movie:
            title = to_download[1]
        else:
            title = to_download[2]

        # Create the megaupload instance
        megafile = MegaFile(link, cache_dir, self.error_callback)
        filename = megafile.cache_file

        # Download the subtitles
        self.download_subtitles(to_download, filename, is_movie)

        # Start the file download
        megafile.start()

        # Wait the megaupload 45 seconds
        if not megafile.downloaded:
            for i in xrange(45, 1, -1):
                loading_dots = "." * (3 - i % 4)
                self.set_status_message("Please wait %d seconds%s" % \
                                    (i, loading_dots))
                time.sleep(1)

        # Wait until the file exists
        file_exists = False
        while not file_exists:
            self.set_status_message("A few seconds left...")
            file_exists = os.path.exists(filename)
            time.sleep(1)

        # Play or Download
        if download_only:
            self.set_status_message("Downloading: %s" % title)
        else:
            self.set_status_message("Now playing: %s" % title)

        # Show the progress bar
        def show_statusbar():
            self.gui.statusbar_progress.set_fraction(0.0)
            self.gui.statusbar_progress.show()

        gobject.idle_add(show_statusbar)

        cache_on_movies = self.config.get_key("cached_percentage_on_movies")
        cached_percentage = self.config.get_key("cached_percentage")
        cached_percentage = cached_percentage / 100.0

        if is_movie and not cache_on_movies:
            cached_percentage = 0.008

        player_location = self.config.get_key("player_location")
        player_args = self.config.get_key("player_arguments").split()

        size = float(megafile.size)
        stop = False
        running = False
        while not stop:
            time.sleep(0.7)

            downloaded = float(megafile.downloaded_size)

            fraction = downloaded / size

            if not download_only:
                if not running and fraction > cached_percentage:
                    player_cmd = [player_location] + player_args + [filename]
                    process = subprocess.Popen(player_cmd)
                    running = True

                if running and process.poll() != None:
                    stop = True

            gobject.idle_add(self.gui.statusbar_progress.set_fraction, fraction)
            gobject.idle_add(self.gui.statusbar_progress.set_text,
                             "%.2f%%" % (fraction * 100))

        gobject.idle_add(self.gui.statusbar_progress.hide)

        # Automatic mark
        if self.config.get_key("automatic_marks"):
            self.gui.mark_selected()

        megafile.released = True

    def download_subtitles(self, to_download, filename, is_movie):
        """
        Download the subtitle if it exists.
        """

        self.set_status_message("Downloading subtitles...")
        subs_filename = filename.split(".mp4", 1)[0]

        try:
            self.pycavane.get_subtitle(to_download, filename=subs_filename,
                                       movie=is_movie)
        except Exception:
            self.set_status_message("Not subtitles found")

    def set_status_message(self, message):
        gobject.idle_add(self.gui.set_status_message, message)
