#!/usr/bin/env python
# coding: utf-8

"""
Gettext. Translation system.
"""

import os
import locale
import gettext
import gtk.glade

from Paths import TRANSLATION_DIR

TRANS_NAME = "messages"


def configure_gettext():
    """ Configures gettext and returns the
    gettext to be used. """

    langs = []

    lc, _ = locale.getdefaultlocale()
    if lc:
        langs.append(lc)

    language = os.environ.get("LANGUAGE", None)
    if language:
        langs += language.split(":")

    gettext.bindtextdomain(TRANS_NAME, TRANSLATION_DIR)
    gettext.textdomain(TRANS_NAME)
    gtk.glade.bindtextdomain(TRANS_NAME, TRANSLATION_DIR)
    gtk.glade.textdomain(TRANS_NAME)

    lang = gettext.translation(TRANS_NAME, TRANSLATION_DIR,
                               languages=langs, fallback=True)

    return lang.gettext

gettext = configure_gettext()
