#!/usr/bin/env python
# coding: utf-8

from guicavane.Paths import HOSTS_IMAGES_DIR, SEP
from Base import BaseDownloader


class Megaupload(BaseDownloader):
    """ Megaupload's Downloader. """

    name = "Megaupload"
    icon_path = HOSTS_IMAGES_DIR + SEP + "megaupload.png"

    def __init__(self, link):
        pass
