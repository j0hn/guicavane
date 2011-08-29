#!/usr/bin/env python
# coding: utf-8

"""
Base Downloader. Every Downloader must be a subclass from this Downloader.
"""

import os
import gtk


class DownloadError(Exception):
    """ Indicates a downloading error. """


class BaseDownloader(object):
    """ Base class for a Downloader. """

    name = ""
    icon_path = ""
    __icon = None

    def __init__(self, gui_manager=None, url=None):
        """ Sets up the basic stuff for a Downloader. """
        self.file_path = None
        self.file_size = None

    @property
    def downloaded_size(self):
        """ Returns the currently downloaded size in bytes. """

        if self.file_path:
            return int(os.path.getsize(self.file_path))

        return 0

    @property
    def icon(self):
        if not self.__icon:
            image = gtk.Image()
            image.set_from_file(self.icon_path)
            self.__icon = image.get_pixbuf()

        return self.__icon

    def process_url(self, play_callback, file_path):
        """ Do the necesary thing such waiting time or asking
        for captcha.
        play_callback is the callback to be called when the file is
        downloading and can be played.
        file_path is the file where to be written on. """

        pass

    def __repr__(self):
        return "<Downloader: name: '%s'>" % self.name
