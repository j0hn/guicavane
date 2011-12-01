#!/usr/bin/env python
# coding: utf-8

import os
import Cuevana  # FIXME: always avaliable because it's guicavane's default

APIS_DIR = os.path.dirname(os.path.abspath(__file__))
AVALIABLE_APIS = []

apis = []
for dirname in os.listdir(APIS_DIR):
    if os.path.isdir(os.path.join(APIS_DIR, dirname)):
        apis.append("guicavane.Hosts." + dirname)

for api in apis:
    try:
        AVALIABLE_APIS.append(__import__(api, fromlist=[api]).api)
    except Exception, error:
        print "Warning: couldn't import %s api: %s" % (api, error)
