#!/usr/bin/env python
# coding: utf-8

import sys

from Dummy import Dummy
from Megaupload import Megaupload
from Bitshare import Bitshare
from Filefactory import Filefactory
from Hotfile import Hotfile
from Wupload import Wupload

DUMMY_ENABLE = False
if "-d" in sys.argv or "--dummy" in sys.argv:
    DUMMY_ENABLE = True

AVALIABLE_HOSTS = {
    "megaupload": Megaupload,
    "bitshare": Bitshare,
    #"filefactory": Filefactory,  #FIXME
    "hotfile": Hotfile,
    "wupload": Wupload,
}

if DUMMY_ENABLE:
    AVALIABLE_HOSTS["dummy"] = Dummy

def get_avaliable():
    return AVALIABLE_HOSTS.keys()

def get(host, gui_manager, link):
    return AVALIABLE_HOSTS[host](gui_manager, link)
