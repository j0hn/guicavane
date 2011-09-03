#!/usr/bin/env python
# coding: utf-8

from Megaupload import Megaupload
from Bitshare import Bitshare
from Filefactory import Filefactory

AVALIABLE_HOSTS = {
    "megaupload": Megaupload,
    "bitshare": Bitshare,
    "filefactory": Filefactory
}

def get_avaliable():
    return AVALIABLE_HOSTS.keys()

def get(host, gui_manager, link):
    return AVALIABLE_HOSTS[host](gui_manager, link)
