#!/usr/bin/env python
# coding: utf-8

"""
Guicavane: graphical user interface for the website cuevana.tv

Uses gtk toolkit to provide the graphical interface of the website
Author: Gonzalo Garcia (A.K.A j0hn) <j0hn.com.ar@gmail.com>
"""

import os
import gtk
import sys
import gobject

from guicavane import GUIHandler


def main():
    """
    Creates the window and starts gtk main loop.
    """

    # Allow correctly opening from outside
    path = os.path.dirname(sys.argv[0])
    if path:
        os.chdir(path)

    # Create the program
    handler = GUIHandler()

    if sys.platform == "win32":
        gobject.threads_init()
    else:
        gtk.gdk.threads_init()

    # Starts main loop
    try:
        gtk.main()
    except KeyboardInterrupt:
        handler.save_config()

if __name__ == "__main__":
    main()
