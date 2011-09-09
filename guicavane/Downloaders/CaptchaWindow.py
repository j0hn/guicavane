#!/usr/bin/env python
# coding: utf-8

"""
Captcha Window. Utility to show an input window with a captcha image.
"""

import gtk
import gobject

from guicavane.Constants import CAPTCHA_GUI_FILE
from guicavane.Paths import TEMP_DIR, SEP

CAPTCHA_IMAGE_PATH = TEMP_DIR + SEP + "recaptcha_image"


class CaptchaWindow(object):
    """ Window with an image of a captcha. The image is
    taken from CAPTCHA_IMAGE_PATH. """

    def __init__(self, gui_manager, ok_callback):
        """ Creates the window but not show it. ok_callback is called when
        the ok button is pressed. """

        self.gui_manager = gui_manager
        self.ok_callback = ok_callback

        self.builder = gtk.Builder()
        self.builder.add_from_file(CAPTCHA_GUI_FILE)
        self.builder.connect_signals(self)

        self.captcha_image = self.builder.get_object("captcha_image")
        self.response_input = self.builder.get_object("response_input")
        self.captcha_window = self.builder.get_object("captcha_window")

    def show(self, *args):
        """ Shows the window. """

        gobject.idle_add(self.gui_manager.set_status_message,
            "Please fill the captcha")

        self.captcha_image.set_from_file(CAPTCHA_IMAGE_PATH)
        self.captcha_window.show_all()

    def get_input_text(self):
        """ Returns the value of the input. """

        return self.response_input.get_text()

    def _on_ok(self, *args):
        """ Called when the ok button is pressed. """
        self.captcha_window.hide()
        self.ok_callback()

    def _on_cancel(self, *args):
        """ Called when the cancel button is pressed. """

        self.gui_manager.unfreeze()
        self.captcha_window.hide()
