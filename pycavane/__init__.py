#!/usr/bin/env python
# coding: utf-8

import os

APIS_DIR = os.path.dirname(os.path.abspath(__file__))

apis = []
files = os.listdir(APIS_DIR)
for filename in files:
    if filename.endswith("api.py") and filename != "base_api.py":
        apis.append("pycavane." + filename.replace(".py", ""))

modules = map(__import__, apis)
