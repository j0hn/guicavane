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
    accept_ranges = False

    def __init__(self, url_open, gui_manager, url):
        """
        Sets up the basic stuff for a Downloader
        and adds headers for the UrlOpen instance.
        """
        self.file_path = None
        self.file_size = 0
        self.stop_downloading = False

        # Cookie headers
        accounts = gui_manager.accounts
        self.account = accounts.get(self.name.lower())
        if self.account and self.account.cookiejar:
            url_open.add_cookies(self.account.cookiejar)

    def add_range(self, url_open):
        """
        Range headers for the UrlOpen instance.
        `file_path' must be set.
        """
        if self.accept_ranges and self.file_path:
            offset = self.downloaded_size
            url_open.add_headers({"Range": "bytes=%s-" % offset})

    def download_to(self, handler, file_path):
        """ Starts a download. handler must be a UrlOpen instance and file_path
        a string with the absolute path to the file to be written on"""

        # Sets the file offset using the request headers
        try:
            field = handler.headers["Content-Range"]

            # Parse: "bytes 0-130480279/130480280"
            field = field[field.find(' ')+1:]
            field = field[:field.find('-')]
            offset = int(field)
        except:
            offset = 0

        # Sets the file size using the request headers
        try:
            self.file_size = float(handler.headers["Content-Length"]) + offset
        except Exception as e:
            self.file_size = 0

        filehandler = open(file_path, "ab")
        filehandler.seek(offset)

        while True:
            data = handler.read(1024)

            if not data or self.stop_downloading:
                filehandler.close()
                break

            filehandler.write(data)
            filehandler.flush()

    @property
    def downloaded_size(self):
        """ Returns the currently downloaded size in bytes. """

        if self.file_path and os.path.exists(self.file_path):
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
