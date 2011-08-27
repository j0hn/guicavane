#!/usr/bin/env python
# coding: utf-8

import gtk


class BaseDownloader(object):
    """ Base class for a Downloader. """

    name = ""
    icon_path = ""
    __icon = None

    def __init__(self, link):
        """ Sets up the basic stuff for a Downloader. """

        raise NotImplementedError()

    @property
    def icon(self):
        if not self.__icon:
            image = gtk.Image()
            image.set_from_file(self.icon_path)
            self.__icon = image.get_pixbuf()

        return self.__icon
