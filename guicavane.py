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
import time
import string
import gobject

import pycavane
from config import Config
from megaupload import MegaFile
from threadrunner import GtkThreadRunner
from constants import MODE_SHOWS, MODE_MOVIES, MODE_FAVORITES, MODES, \
                      ICON_FILE_MOVIE, ICON_FOLDER


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
    """
    Main class, loads the gui and handles all events.
    """

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
        self.name_filter_clear = self.builder.get_object("nameFilterClear")
        self.name_list = self.builder.get_object("nameList")
        self.name_model = self.name_list.get_model()
        self.file_filter = self.builder.get_object("fileFilter")
        self.file_filter_clear = self.builder.get_object("fileFilterClear")
        self.file_viewer = self.builder.get_object("fileViewer")
        self.file_model = self.file_viewer.get_model()
        self.mode_combo = self.builder.get_object("modeCombo")

        # Creating a new filter model to allow the user filter the
        # shows and movies by typing on an entry box
        self.name_model_filter = self.name_model.filter_new()
        self.name_model_filter.set_visible_func(generic_visible_func,
                                                (self.name_filter, 0))
        self.name_list.set_model(self.name_model_filter)

        self.file_model_filter = self.file_model.filter_new()
        self.file_model_filter.set_visible_func(generic_visible_func,
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

        self.current_seasson = None

        # Get and set the last used mode
        last_mode = self.config.get_key("last_mode")
        if last_mode not in MODES:
            last_mode = MODE_SHOWS
        last_mode = last_mode.lower()

        # Set the combobox in the right mode
        self.mode_combo.set_active(MODES.index(MODE_FAVORITES))

        getattr(self, "set_mode_%s" % last_mode)()

    def freeze(self):  # TODO: parameter to set the status message?
        """
        Freezes the gui so the user can't interact with it.
        """

        self.mode_combo.set_sensitive(False)
        self.name_list.set_sensitive(False)
        self.name_filter.set_sensitive(False)
        self.name_filter_clear.set_sensitive(False)
        self.file_viewer.set_sensitive(False)
        self.file_filter.set_sensitive(False)
        self.file_filter_clear.set_sensitive(False)
        self.set_status_message("Loading...")

    def unfreeze(func):
        """
        Decorator that calls the decorated function and then unfreezes
        the gui so the user can interact with it.
        """

        def decorate(self, *args, **kwargs):
            args = [self] + list(args)  # func is a method so it needs self
            func(*args, **kwargs)

            self.set_status_message("")
            self.mode_combo.set_sensitive(True)
            self.name_list.set_sensitive(True)
            self.name_filter.set_sensitive(True)
            self.name_filter_clear.set_sensitive(True)
            self.file_viewer.set_sensitive(True)
            self.file_filter.set_sensitive(True)
            self.file_filter_clear.set_sensitive(True)

        return decorate

    def background_task(self, func, callback, *args, **kwargs):
        """
        Freezes the gui, starts a thread with func and when it's
        over calls callback with the result.
        """

        self.freeze()
        GtkThreadRunner(callback, func, *args, **kwargs)

    def set_status_message(self, message):
        """
        Sets the message shown in the statusbar.
        """

        context_id = self.statusbar.get_context_id("Messages")
        self.statusbar.push(context_id, message)

    def _on_destroy(self, *args):
        """
        Called when the window closes.
        """

        # Save the config to disk
        self.config.save()

        # We kill gtk
        gtk.main_quit()

    def _on_mode_change(self, *args):
        """
        Called when the 'mode' combobox changes value.
        """

        mode = self.get_mode()
        self.config.set_key("last_mode", mode)
        mode = mode.lower()

        self.file_model.clear()

        # Call the corresponding set_mode method
        getattr(self, "set_mode_%s" % mode)()

    def _on_name_change(self, *args):
        """
        Called when the user selects a movie or a show from the 'name list'.
        """

        selected_text = self.get_selected_name()

        self.file_model.clear()
        mode = self.get_mode()

        if mode == MODE_SHOWS or mode == MODE_FAVORITES:
            self.background_task(self.pycavane.seasson_by_show,
                                 self.show_seassons, selected_text)
        else:
            pass  # TODO: movies

    def _on_name_filter_change(self, *args):
        """
        Called when the textbox to filter names changes.
        """

        self.name_model_filter.refilter()

    def _on_name_filter_clear_clicked(self, *args):
        """
        Clears the name filter input.
        """

        self.name_filter.set_text("")

    def _on_name_button_press(self, view, event):
        """
        Called when the user press any mouse button on the name list.
        """

        if event.button == 3:

            if self.get_mode() == MODE_FAVORITES:
                popup_menu = self.builder.get_object("nameFavoritesMenu")
            else:
                popup_menu = self.builder.get_object("nameShowsMenu")

            popup_menu.popup(None, None, None, event.button, event.time)

    def _on_name_add_favorite(self, *args):
        """
        Adds the selected show from favorites.
        """

        selected = self.get_selected_name()
        if selected not in self.config.get_key("favorites"):
            self.config.append_key("favorites", selected)

    def _on_name_remove_favorite(self, *args):
        """
        Removes the selected show from favorites.
        """

        selected = self.get_selected_name()
        if selected in self.config.get_key("favorites"):
            self.config.remove_key("favorites", selected)
            self.set_mode_favorites()

    def _on_file_filter_change(self, *args):
        """
        Called when the textbox to filter files changes.
        """

        self.file_model_filter.refilter()

    def _on_file_filter_clear_clicked(self, *args):
        """
        Clears the file filter input.
        """

        self.file_filter.set_text("")

    def _on_open_file(self, widget, path, *args):
        """
        Called when the user double clicks on a file inside the file viewer.
        """

        selected_text = self.file_model[path][1]

        mode = self.get_mode()
        if mode == MODE_SHOWS or mode == MODE_FAVORITES:
            if selected_text.startswith("Temporada"):
                self.open_seasson(selected_text)
            else:
                self.open_show(selected_text)
        elif mode == MODE_MOVIES:
            self.open_movie(selected_text)

    def _on_about_clicked(self, *args):
        """
        Opens the about dialog.
        """

        help_dialog = self.builder.get_object("aboutDialog")
        help_dialog.run()
        help_dialog.hide()

    def _on_open_settings(self, *args):
        """
        Called when the user opens the preferences from the menu.
        """

        player_cmd = self.builder.get_object("playerCommandEntry")
        cache_dir = self.builder.get_object("cacheDirEntry")

        player_cmd.set_text(self.config.get_key("player_command"))
        cache_dir.set_text(self.config.get_key("cache_dir"))
        self.settings_dialog.run()
        self.settings_dialog.hide()

    def _on_save_settings(self, *args):
        """
        Saves the settings to the disk.
        """

        player_cmd = self.builder.get_object("playerCommandEntry").get_text()
        cache_dir = self.builder.get_object("cacheDirEntry").get_text()

        self.config.set_key("player_command", player_cmd)
        self.config.set_key("cache_dir", cache_dir)
        self.config.save()
        self.settings_dialog.hide()

    @unfreeze
    def show_shows(self, shows):
        """
        Adds all the shows to the list.
        """

        self.file_model.clear()

        for _, show_name in shows:
            self.name_model.append([show_name])

    @unfreeze
    def show_seassons(self, seassons):
        """
        Fills the file viewer with the seassons.
        """

        self.file_model.clear()

        for _, seasson_name in seassons:
            self.file_model.append((ICON_FOLDER, seasson_name))

    @unfreeze
    def show_episodes(self, episodes):
        """
        Fills the file viewer with the episodes.
        """

        self.file_model.clear()

        for _, episode_number, episode_name in episodes:
            episode_name = "%.2d - %s" % (int(episode_number), episode_name)
            self.file_model.append((ICON_FILE_MOVIE, episode_name))

    def open_seasson(self, seasson_text):
        """
        Fills the file viewer with the episodes from the seasson.
        """

        show = self.get_selected_name()
        self.current_seasson = seasson_text
        self.background_task(self.pycavane.episodes_by_season,
                        self.show_episodes, show, seasson_text)

    def open_show(self, episode_text):
        """
        Starts the download of the given episode.
        """

        selected_episode = episode_text.split(" - ", 1)[1]
        show = self.get_selected_name()
        seasson = self.current_seasson

        for episode in self.pycavane.episodes_by_season(show, seasson):
            if episode[2] == selected_episode:
                episode_found = episode
                break

        self.background_task(self.download_file,
                             self.close_show, episode_found)

    @unfreeze
    def close_show(self, *args):
        """
        Called when the user closes the player.
        """

        # Nothing to do yet
        pass

    def open_movie(self, movie_text):
        """
        Starts the download of the given movie.
        """

        print "Open %s" % movie_text

    def download_file(self, episode):
        """
        Given an episode, downloads the subtitles then starts downloading
        the file and starts the player.
        """

        link = self.pycavane.get_direct_links(episode, host="megaupload")
        if link:
            link = link[1]
        else:
            raise Exception("Not download source found")

        cache_dir = self.config.get_key("cache_dir")
        filename = cache_dir + os.sep + link.rsplit('/', 1)[1]

        # Download the subtitle if it exists
        try:
            self.set_status_message("Downloading subtitles...")
            self.pycavane.get_subtitle(episode, filename=filename)
        except:
            self.set_status_message("Not subtitles found")

        megafile = MegaFile(link, cache_dir)
        megafile.start()

        self.waiting_time = 45
        gobject.timeout_add_seconds(1, self.update_waiting_message)

        time.sleep(45)  # Megaupload's 45

        filename = megafile.cache_file
        file_exists = False
        while not file_exists:  # Wait untile the file exists
            self.set_status_message("A phew seconds left...")
            file_exists = os.path.exists(filename)
            time.sleep(2)

        self.set_status_message("Now playing: %s" % episode[2])
        player_command = self.config.get_key("player_command")
        os.system(player_command % filename)
        megafile.released = True

    def update_waiting_message(self):
        """
        Updates the status bar with the remaining time of wait.
        """

        if self.waiting_time == 0:
            del self.waiting_time
            return False
        else:
            loading_dots = "." * (3 - self.waiting_time % 4)
            self.set_status_message("Please wait %d seconds%s" %
                                   (self.waiting_time, loading_dots))
            self.waiting_time -= 1
            return True

    def set_mode_shows(self, *args):
        """
        Sets the current mode to shows.
        """

        self.name_model.clear()
        self.background_task(self.pycavane.get_shows, self.show_shows)

    def set_mode_movies(self):
        """
        Sets the current mode to movies.
        """

        self.name_model.clear()

        for letter in string.uppercase:
            self.name_model.append([letter])

    def set_mode_favorites(self):
        """
        Sets the current mode to favorites.
        """

        self.name_model.clear()
        for favorite in self.config.get_key("favorites"):
            self.name_model.append([favorite])

    def get_mode(self):
        """
        Returns the current mode.
        i.e the value of the mode combobox.
        The result will be the constant MODE_* (see constants definitions).
        """

        model = self.mode_combo.get_model()
        active = self.mode_combo.get_active()
        mode_text = model[active][0]

        # Poscondition
        assert mode_text in MODES

        return mode_text

    def get_selected_name(self):
        """
        Returns the string of the selected item on the 'name list'.
        """

        selection = self.name_list.get_selection()
        model, iteration = selection.get_selected()
        selected_text = model.get_value(iteration, 0)

        return selected_text


def generic_visible_func(model, iteration, (entry, text_column)):
    """
    Filters the treeview based on the text found on `entry`.
    text_column should be the column index where the text can be
    found.
    """

    filtered_text = entry.get_text()

    row_text = model.get_value(iteration, text_column)

    if row_text:
        # Case insensitive search
        filtered_text = filtered_text.lower()
        row_text = row_text.lower()

        return filtered_text in row_text

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
    Guicavane(gui_file, config_file)
    gtk.gdk.threads_init()
    gtk.main()

if __name__ == "__main__":
    main()
