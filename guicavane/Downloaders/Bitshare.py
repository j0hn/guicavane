#!/usr/bin/env python
# coding: utf-8

import gtk

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Bitshare(BaseDownloader):
    """ Bitshare's Downloader. """

    name = "Bitshare"
    icon_path = HOSTS_IMAGES_DIR + SEP + "bitshare.png"

    def __init__(self, link):
        pass
