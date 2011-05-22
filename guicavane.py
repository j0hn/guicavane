#!/usr/bin/evn python
# coding: utf-8
"""
guicavane: graphical user interface for the website cuevana.tv

Uses gtk toolkit to provide the graphical interface of the website
Author: Gonzalo Garcia (A.K.A j0hn) <j0hn.com.ar@gmail.com>
"""

import os
import sys
import gtk
import glib
import time
import Queue
import string
import logging
import threading

import pycavane
from config import Config
from megaupload import MegaFile

# Constants
MODE_SHOWS = "Shows"
MODE_MOVIES = "Movies"
MODE_FAVORITES = "Favorites"
MODES = [MODE_SHOWS, MODE_MOVIES, MODE_FAVORITES]
# NOTE: MODES must be in the same order as they appear in the combobox


# Just a useful function
def combobox_get_active_text(combobox):
    """
    Returns the text of the active item of a gtk combobox.
    """

    model = combobox.get_model()
    active = combobox.get_active()

    if active < 0:
        return None

    return model[active][0]


class GtkThreadRunner(threading.Thread):
    """
    Run *func* in a thread with *args* and *kwargs* as arguments, when
    finished call callback with a two item tuple containing a boolean as first
    item informing if the function returned correctly and the returned value or
    the exception thrown as second item
    """

    def __init__(self, callback, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.callback = callback
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.result = Queue.Queue()

        self.start()
        glib.timeout_add(500, self.check)

    def run(self):
        """
        Main function of the thread, run func with args and kwargs
        and get the result, call callback with the (True, result)

        if an exception is thrown call callback with (False, exception)
        """

        try:
            result = (True, self.func(*self.args, **self.kwargs))
        except Exception, ex:
            result = (False, ex)

        self.result.put(result)

    def check(self):
        """
        Check if func finished.
        """

        try:
            result = self.result.get(False, 0.1)
        except Queue.Empty:
            return True

        self.callback(result)
        return False


class ErrorDialog(gtk.MessageDialog):
    """
    Simple error dialog.
    """

    def __init__(self, message, parent=None):
        gtk.MessageDialog.__init__(self, parent, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
        self.run()
        self.destroy()


class WarningDialog(gtk.MessageDialog):
    """
    Simple warning dialog.
    """

    def __init__(self, message, parent=None):
        gtk.MessageDialog.__init__(self, parent, gtk.DIALOG_MODAL,
                                  gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
        self.run()
        self.destroy()


class Guicavane:

    def __init__(self, gui_file, config_file):
        """
        Creates the main window based on the glade file `gui_file`.
        """

        # Precondition: must have gui_file
        assert os.path.exists(gui_file)

        self.builder = gtk.Builder()
        self.builder.add_from_file(gui_file)

        # Config
        self.config = Config(config_file)

        # Getting the used widgets
        self.main_window = self.builder.get_object("mainWindow")
        self.settings_dialog = self.builder.get_object("settingsDialog")
        self.statusbar = self.builder.get_object("statusbar")
        self.name_filter = self.builder.get_object("nameFilter")
        self.name_list = self.builder.get_object("nameList")
        self.name_model = self.name_list.get_model()
        self.file_filter = self.builder.get_object("fileFilter")
        self.file_viewer = self.builder.get_object("fileViewer")
        self.file_model = self.file_viewer.get_model()
        self.seassons_combo = self.builder.get_object("seassonCombo")
        self.seassons_model = self.seassons_combo.get_model()
        self.mode_combo = self.builder.get_object("modeCombo")

        # Creating a new filter model to allow the user filter the
        # shows and movies by typing on an entry box
        self.name_model_filter = self.name_model.filter_new()
        self.name_model_filter.set_visible_func(self.visible_func,
                                                (self.name_filter, 0))
        self.name_list.set_model(self.name_model_filter)

        self.file_model_filter = self.file_model.filter_new()
        self.file_model_filter.set_visible_func(self.visible_func,
                                                (self.file_filter, 1))
        self.file_viewer.set_model(self.file_model_filter)

        # We leave the magic connection to glade
        self.builder.connect_signals(self)

        # Focusing on the name filter
        self.name_filter.grab_focus()  # TODO: not working

        # Now we show the window
        self.main_window.show_all()

        # Loading the API
        cache_dir = self.config.get_key("cache_dir")
        if cache_dir[-1] == os.sep:
            cache_dir = cache_dir[:-1]
        try:
            self.pycavane = pycavane.Pycavane("guicavane", "guicavane",
                                              cache_dir=cache_dir)
        except Exception, error:
            self.pycavane = pycavane.Pycavane()
            if "Login fail" in error.message:
                print "LOGIN FAIL"
                # TODO: show warning dialog
            else:
                print "UNKNOWN ERROR: %s" % error

        self.setup()

    def setup(self):
        """
        Sets the default things.
        """

        # Get and set the last used mode
        last_mode = self.config.get_key("last_mode")
        if last_mode not in MODES:
            last_mode = MODE_SHOWS
        last_mode = last_mode.lower()
        getattr(self, "set_mode_%s" % last_mode)()

    def freeze_gui(self):
        """
        Freezes the gui so the user can't interact with it.
        """

        self.mode_combo.set_sensitive(False)
        self.seassons_combo.set_sensitive(False)
        self.name_list.set_sensitive(False)
        self.file_viewer.set_sensitive(False)
        self.name_filter.set_sensitive(False)
        self.file_filter.set_sensitive(False)
        self.seassons_combo.set_sensitive(False)
        self.set_status_message("Loading...")

    def unfreeze_gui(self, result):
        """
        Free the gui so the user can interact with it.
        """

        self.set_status_message("")
        self.mode_combo.set_sensitive(True)
        self.seassons_combo.set_sensitive(True)
        self.name_list.set_sensitive(True)
        self.file_viewer.set_sensitive(True)
        self.name_filter.set_sensitive(True)
        self.file_filter.set_sensitive(True)
        self.seassons_combo.set_sensitive(True)

        if not result[0]:
            print "Error", result[1]
            self.set_status_message("Error: %s" % result[1])
            # TODO: check why this locks the gui
            # ErrorDialog("An error has ocurred\nDetails: %s" % result[1])

    def background_task(func):
        """
        Decorator to start a function in background and not
        block the interface.
        """

        def decorate(self, *args, **kwargs):
            self.freeze_gui()
            GtkThreadRunner(self.unfreeze_gui, func,
                            *([self] + list(args)), **kwargs)

        return decorate

    def set_status_message(self, message):
        """
        Sets the message shown in the statusbar.
        """

        context_id = self.statusbar.get_context_id("Messages")
        self.statusbar.push(context_id, message)

    def on_destroy(self, widget):
        """
        Called when the window closes.
        """

        # Save the config to disk
        self.config.save()

        # We kill gtk
        gtk.main_quit()

    def on_mode_change(self, combo):
        """
        Called when the 'mode' combobox changes value.
        """

        mode = self.get_mode()
        self.config.set_key("last_mode", mode)
        mode = mode.lower()

        self.file_model.clear()

        # Call the corresponding set_mode method
        getattr(self, "set_mode_%s" % mode)()

    @background_task
    def on_seasson_change(self, combo):
        """
        Called when the 'seasson' combobox changes value.
        This will only be fired if the 'mode' combobox is setted to 'Shows'.
        """

        # Precondition
        if self.get_mode() != MODE_SHOWS:
            return

        seasson = combobox_get_active_text(combo)
        show = self.get_selected_name()

        if not seasson:
            return

        self.file_model.clear()

        file_image = gtk.Image()
        file_image.set_from_file("images/video_file.png")
        file_icon = file_image.get_pixbuf()

        seasson = "Temporada " + seasson  # Hopfully temporary fix
        for episode in self.pycavane.episodes_by_season(show, seasson):
            episode_name = "%.2d - %s" % (int(episode[1]), episode[2])
            append_item_to_store(self.file_model, (file_icon, episode_name))

    @background_task
    def on_name_change(self, treeview):
        """
        Called when the user selects a movie or a show from the 'name list'.
        """

        selected_text = self.get_selected_name()

        self.file_model.clear()
        if self.get_mode() == MODE_SHOWS:
            self.seassons_model.clear()

            seassons = self.pycavane.seasson_by_show(selected_text)
            for i in seassons:
                seasson_number = i[1].split("Temporada ")[1]
                append_item_to_store(self.seassons_model, [seasson_number])

        else:
            self.file_model.clear()

            file_image = gtk.Image()
            file_image.set_from_file("images/video_file.png")
            file_icon = file_image.get_pixbuf()

            letter = selected_text

            for movie in self.pycavane.get_movies(letter):
                append_item_to_store(self.file_model, (file_icon, movie[1]))

    def on_name_filter_change(self, entry):
        """
        Called when the textbox to filter names changes.
        """

        self.name_model_filter.refilter()

    def on_name_filter_clear_clicked(self, button):
        self.name_filter.set_text("")

    def on_file_filter_change(self, entry):
        """
        Called when the textbox to filter files changes.
        """

        self.file_model_filter.refilter()

    def on_file_filter_clear_clicked(self, button):
        self.file_filter.set_text("")

    def on_open_file(self, widget, path, *args):
        """
        Called when the user double clicks on a file inside the file viewer.
        """

        item_text = self.file_model[path][1]

        if self.get_mode() == MODE_SHOWS:
            self.open_show(item_text)
        elif self.get_mode() == MODE_MOVIES:
            self.open_movies(item_text)

    def open_show(self, episode_text):
        """
        Starts the download of the given episode.
        """

        selected_episode = episode_text.split(" - ", 1)[1]

        seasson = combobox_get_active_text(self.seassons_combo)
        show = self.get_selected_name()

        seasson = "Temporada " + seasson  # Hopfully temporary fix
        for episode in self.pycavane.episodes_by_season(show, seasson):
            if selected_episode == episode[2]:
                episode_found = episode
                break

        self.download_file(episode_found)

    def open_move(self, movie_text):
        """
        Starts the download of the given movie.
        """

        print "Open %s" % movie_text

    @background_task
    def download_file(self, episode):
        """
        Given an episode, downloads the subtitles then starts downloading
        the file and starts the player.
        """

        self.file_viewer.set_sensitive(False)

        link = self.pycavane.get_direct_links(episode, host="megaupload")
        if link:
            link = link[1]
        else:
            raise Exception("Not download source found")

        cache_dir = self.config.get_key("cache_dir")
        filename = cache_dir + os.sep + link.rsplit('/', 1)[1]

        # Download the subtitle if it exists
        try:
            subtitle = self.pycavane.get_subtitle(episode, filename=filename)
        except:
            self.set_status_message("Not subtitles found")

        megafile = MegaFile(link, cache_dir)
        megafile.start()

        self.waiting_time = 45
        glib.timeout_add_seconds(1, self.update_waiting_message)

        time.sleep(45)  # Megaupload's 45

        filename = megafile.cache_file
        file_exists = False
        while not file_exists:  # Wait untile the file exists
            file_exists = os.path.exists(filename)
            time.sleep(5)

        self.set_status_message("Now playing: %s" % episode[2])
        player_command = self.config.get_key("player_command")
        os.system(player_command % filename)
        megafile.released = True

    def update_waiting_message(self):
        if self.waiting_time == 0:
            del self.waiting_time
            return False
        else:
            loading_dots = "." * (3 - self.waiting_time % 4)
            self.set_status_message("Please wait %d seconds%s" %
                                   (self.waiting_time, loading_dots))
            self.waiting_time -= 1
            return True

    @background_task
    def set_mode_shows(self, *args):
        """
        Sets the current mode to shows.
        """

        # Set the combobox in case it isn't in the right mode
        self.mode_combo.set_active(MODES.index(MODE_SHOWS))

        # We show the seasson combobox
        self.seassons_combo.set_sensitive(True)

        self.name_model.clear()

        shows = self.pycavane.get_shows()
        for show in shows:
            #self.name_model.append([show[1]])
            append_item_to_store(self.name_model, (show[1],))

    def set_mode_movies(self):
        """
        Sets the current mode to movies.
        """

        # Set the combobox in case it isn't in the right mode
        self.mode_combo.set_active(MODES.index(MODE_MOVIES))

        # We won't be needing the seasson combobox so we hide it
        self.seassons_combo.set_sensitive(False)

        self.name_model.clear()

        for letter in string.uppercase:
            append_item_to_store(self.name_model, (letter,))

    def set_mode_favorites(self):
        """
        Sets the current mode to favorites.
        """

        # Set the combobox in case it isn't in the right mode
        self.mode_combo.set_active(MODES.index(MODE_FAVORITES))

        self.name_model.clear()

    def get_mode(self):
        """
        Returns the current mode.
        i.e the value of the mode combobox.
        The result will be the constant MODE_* (see constants definitions).
        """

        mode_text = combobox_get_active_text(self.mode_combo)

        # Poscondition
        assert mode_text in MODES

        return mode_text

    def get_selected_name(self):
        """
        Returns the string of the selected item on the 'name list'.
        """

        selection = self.name_list.get_selection()
        model, iter = selection.get_selected()
        selected_text = model.get_value(iter, 0)

        return selected_text

    def visible_func(self, model, iter, (entry, text_column)):
        filtered_text = entry.get_text()

        row_text = model.get_value(iter, text_column)

        if row_text:
            # Case insensitive search
            filtered_text = filtered_text.lower()
            row_text = row_text.lower()

            return filtered_text in row_text

        return False

    def on_about_clicked(self, *args):
        help_dialog = self.builder.get_object("aboutDialog")
        help_dialog.run()
        help_dialog.hide()

    def on_open_settings(self, button):
        player_cmd = self.builder.get_object("playerCommandEntry")
        cache_dir = self.builder.get_object("cacheDirEntry")

        player_cmd.set_text(self.config.get_key("player_command"))
        cache_dir.set_text(self.config.get_key("cache_dir"))
        self.settings_dialog.run()
        self.settings_dialog.hide()

    def on_save_settings(self, *args):
        player_cmd = self.builder.get_object("playerCommandEntry").get_text()
        cache_dir = self.builder.get_object("cacheDirEntry").get_text()

        self.config.set_key("player_command", player_cmd)
        self.config.set_key("cache_dir", cache_dir)
        self.config.save()
        self.settings_dialog.hide()


def append_item_to_store(store, item):
    store.append(item)
    return False


def main():
    """
    Creates the window and starts gtk main loop.
    """
    path = os.path.dirname(sys.argv[0])
    if path:
        # Allow correctly opening from outside
        os.chdir(path)

    gui_file = "gui.glade"
    config_file = os.path.expanduser("~") + os.sep + ".guicavane.conf"
    guicavane = Guicavane(gui_file, config_file)
    gtk.gdk.threads_init()
    gtk.main()

if __name__ == "__main__":
    main()
