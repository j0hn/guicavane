#!/usr/bin/evn python
# coding: utf-8

"""
guicavana: graphical user interface for the website cuevana.tv

Uses gtk toolkit to provide the graphical interface of the website
Author: Gonzalo Garcia (A.K.A j0hn) <j0hn.com.ar@gmail.com>
"""

import gtk

from utils import combobox_get_active_text


class MainWindow:

    def __init__(self, guifile):
        """
        Creates the main window based on the glade file `guifile`.
        """

        # MUST have gui file
        assert(guifile)

        self.builder = gtk.Builder()
        self.builder.add_from_file(guifile)

        self.window = self.builder.get_object("mainWindow")
        self.window.show_all()

        self.builder.connect_signals(self)

    def on_destroy(self, widget):
        """
        Called when the window closes.
        """

        # We kill gtk
        gtk.main_quit()


    def on_mode_change(self, combo):
        """
        Called when the 'mode' combobox changes value.
        """

        mode = combobox_get_active_text(combo)

        seasson_combo = self.builder.get_object("seassonCombo")

        if mode == "Series":
            seasson_combo.set_sensitive(True)
        else:
            seasson_combo.set_sensitive(False)

    def on_seasson_change(self, combo):
        """
        Called when the 'seasson' combobox changes value.
        This will only be fired if the 'mode' combobox is setted to 'Series'.
        """

        # Precondition
        mode_combobox = self.builder.get_object("modeCombo")
        mode_text = combobox_get_active_text(mode_combobox)
        assert mode_text == "Series"


        print combobox_get_active_text(combo)


def main():
    """
    Creates the window and starts gtk main loop.
    """

    guifile = "gui.glade"
    mainWindow = MainWindow(guifile)
    gtk.main()


if __name__ == "__main__":
    main()
