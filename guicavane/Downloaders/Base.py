#!/usr/bin/env python
# coding: utf-8

import gtk


class BaseDownloader(object):
    """ Base class for a Downloader. """

    name = ""
    icon_path = ""
    __icon = None

    def __init__(self, gui_manager, url):
        """ Sets up the basic stuff for a Downloader. """

        raise NotImplementedError()

    @property
    def icon(self):
        if not self.__icon:
            image = gtk.Image()
            image.set_from_file(self.icon_path)
            self.__icon = image.get_pixbuf()

        return self.__icon

    def process(self, play_file):
        """ Do the necesary thing such waiting time or asking
        for captcha.
        play_file is the callback to be called when the file is
        downloading and can be played. """

        pass
