#!/usr/bin/env python
# coding: utf-8

from Megaupload import Megaupload
from Bitshare import Bitshare

AVALIABLE_HOSTS = {
    "megaupload": Megaupload,
    "bitshare": Bitshare,
}

def get_avaliable():
    return AVALIABLE_HOSTS.keys()

def get(host, link):
    return AVALIABLE_HOSTS[host](link)
