#!/usr/bin/env python

import os
import sys

PATH = os.path.dirname(sys.argv[0])
if PATH:
    os.chdir(PATH)

FILES = ["build\\gui\\main.glade", "build\\gui\\settings.glade"]


for file in FILES:
    with open(file) as read_fh:
        data = read_fh.read()
        data = data.replace("../../images/", "..\\images\\")
        write_fh = open(file, "w")
        write_fh.write(data)