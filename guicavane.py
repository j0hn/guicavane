#!/usr/bin/evn python
# coding: utf-8

"""
Guicavane: graphical user interface for the website cuevana.tv

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
from constants import *


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

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(gui_file)

        # Config
        self.config = Config(config_file)

        # Attributes
        self.current_show = None
        self.current_seasson = None
        self.current_movies = {}
        self.download_error = False
        self.waiting_time = 45

        # Getting the used widgets
        self.main_window = self.builder.get_object("mainWindow")
        self.settings_dialog = self.builder.get_object("settingsDialog")
        self.statusbar = self.builder.get_object("statusbar")
        self.name_filter = self.builder.get_object("nameFilter")
        self.name_filter_clear = self.builder.get_object("nameFilterClear")
        self.name_list = self.builder.get_object("nameList")
        self.name_model = self.name_list.get_model()
        self.file_viewer = self.builder.get_object("fileViewer")
        self.file_model = self.file_viewer.get_model()
        self.mode_combo = self.builder.get_object("modeCombo")
        self.search_entry = self.builder.get_object("searchEntry")
        self.search_button = self.builder.get_object("searchButton")
        self.search_clear = self.builder.get_object("searchClear")
        self.sidebar = self.builder.get_object("sidebarVbox")
        self.path_label = self.builder.get_object("pathLabel")

        # Creating a new filter model to allow the user filter the
        # shows and movies by typing on an entry box
        self.name_model_filter = self.name_model.filter_new()
        self.name_model_filter.set_visible_func(generic_visible_func,
                                          (self.name_filter, NAME_COLUMN_TEXT))
        self.name_list.set_model(self.name_model_filter)

        # We leave the magic connection to glade
        self.builder.connect_signals(self)

        # Keyboard shortcuts
        accel_group = gtk.AccelGroup()
        key, modifier = gtk.accelerator_parse("<Ctrl>W")
        accel_group.connect_group(key, modifier, gtk.ACCEL_VISIBLE,
                                  lambda a, b, c, d: gtk.main_quit())
        key, modifier = gtk.accelerator_parse("<Ctrl>Q")
        accel_group.connect_group(key, modifier, gtk.ACCEL_VISIBLE,
                                  lambda a, b, c, d: gtk.main_quit())
        self.main_window.add_accel_group(accel_group)

        # Now we show the window
        self.main_window.show_all()

        # Loading the API
        cache_dir = self.config.get_key("cache_dir")
        if cache_dir[-1] == os.sep:
            cache_dir = cache_dir[:-1]

        self.pycavane = pycavane.Pycavane(cache_dir=cache_dir)

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

        # Set the combobox in the right mode
        self.mode_combo.set_active(MODES.index(last_mode))

        last_mode = last_mode.lower()
        getattr(self, "set_mode_%s" % last_mode)()

    def freeze(self, status_message="Loading..."):
        """
        Freezes the gui so the user can't interact with it.
        """

        self.mode_combo.set_sensitive(False)
        self.name_list.set_sensitive(False)
        self.name_filter.set_sensitive(False)
        self.name_filter_clear.set_sensitive(False)
        self.file_viewer.set_sensitive(False)
        self.search_entry.set_sensitive(False)
        self.search_clear.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self.set_status_message(status_message)

    def unfreeze(func):
        """
        Decorator that calls the decorated function and then unfreezes
        the gui so the user can interact with it.
        """

        def decorate(self, *args, **kwargs):
            """
            Decorated function.
            """

            self._unfreeze()

            args = [self] + list(args)  # func is a method so it needs self
            func(*args, **kwargs)


        return decorate

    def _unfreeze(self):
        """
        Sets the widgets to be usable.
        Usually this function shouldn't be called directly but using the
        decorator @unfreeze but is not completly wrong to use it.
        """
        self.set_status_message("")
        self.mode_combo.set_sensitive(True)
        self.name_list.set_sensitive(True)
        self.name_filter.set_sensitive(True)
        self.name_filter_clear.set_sensitive(True)
        self.file_viewer.set_sensitive(True)
        self.search_entry.set_sensitive(True)
        self.search_clear.set_sensitive(True)
        self.search_button.set_sensitive(True)

    def background_task(self, func, callback, *args, **kwargs):
        """
        Freezes the gui, starts a thread with func and when it's
        over calls callback with the result.
        """

        status_message = "Loading..."
        if "status_message" in kwargs:
            status_message = kwargs["status_message"]
            del kwargs["status_message"]

        self.freeze(status_message)
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
        Called when the user selects a show from the 'name list'.
        """

        selected_text = get_selected_text(self.name_list, NAME_COLUMN_TEXT)
        self.current_show = selected_text

        self.path_label.set_text(self.current_show)

        self.file_model.clear()

        self.background_task(self.pycavane.seasson_by_show,
                       self.show_seassons, selected_text,
                       status_message="Loading show %s..." % selected_text)

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

        if event.button == 3:  # 3 it's right click
            if self.get_mode() == MODE_FAVORITES:
                popup_menu = self.builder.get_object("nameFavoritesMenu")
            else:
                popup_menu = self.builder.get_object("nameShowsMenu")

            popup_menu.popup(None, None, None, event.button, event.time)

    def _on_name_add_favorite(self, *args):
        """
        Adds the selected show from favorites.
        """

        selected = get_selected_text(self.name_list, NAME_COLUMN_TEXT)
        if selected not in self.config.get_key("favorites"):
            self.config.append_key("favorites", selected)

    def _on_name_remove_favorite(self, *args):
        """
        Removes the selected show from favorites.
        """

        selected = get_selected_text(self.name_list, NAME_COLUMN_TEXT)
        if selected in self.config.get_key("favorites"):
            self.config.remove_key("favorites", selected)
            self.set_mode_favorites()

    def _on_file_button_press(self, view, event):
        """
        Called when the user press any mouse button on the file viewer.
        """

        if event.button == 3:
            popup_menu = self.builder.get_object("fileViewerMenu")

            selected_text = get_selected_text(self.file_viewer,
                                              FILE_VIEW_COLUMN_TEXT)
            if not selected_text.startswith("Temporada"):
                popup_menu.popup(None, None, None, event.button, event.time)

    def _on_play_clicked(self, *args):
        """
        Called when the user click on the play context menu item.
        """

        selected_text = get_selected_text(self.file_viewer,
                                          FILE_VIEW_COLUMN_TEXT)
        if selected_text.count(" - "):  # It's an episode. I know this is ugly
            self.open_show(selected_text)
        else:
            self.open_movie(selected_text)

    def _on_download_only_clicked(self, *args):
        """
        Called when the user click on the download only context menu item.
        """

        self._on_download_clicked(None, True)

    def _on_download_clicked(self, widget, download_only=False):
        """
        Called when the user click on the download and play context menu item.
        """

        chooser = gtk.FileChooserDialog(title="Dowload to...",
                  parent=self.main_window, action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                  gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        last_download_dir = self.config.get_key("last_download_directory")
        chooser.set_current_folder(last_download_dir)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:

            save_to = chooser.get_filename()
            self.config.set_key("last_download_directory", save_to)

            selected_text = get_selected_text(self.file_viewer,
                                              FILE_VIEW_COLUMN_TEXT)

            if self.get_mode() == MODE_MOVIES:
                self.open_movie(selected_text, file_path=save_to,
                                download_only=download_only)
            else:
                self.open_show(selected_text, file_path=save_to,
                               download_only=download_only)

        chooser.destroy()

    def _on_mark_clicked(self, *args):
        """
        Called when the user clicks on Mark item in the context menu.
        """

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        selected_text = model.get_value(iteration, FILE_VIEW_COLUMN_TEXT)
        model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE_MARK)

        self.config.append_key("marks", selected_text)

    def _on_unmark_clicked(self, *args):
        """
        Called when the user clicks on Mark item in the context menu.
        """

        marks = self.config.get_key("marks")

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        selected_text = model.get_value(iteration, FILE_VIEW_COLUMN_TEXT)

        if selected_text in marks:
            model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE)
            self.config.remove_key("marks", selected_text)

    def _on_search_clear_clicked(self, *args):
        """
        Clears the search input.
        """

        self.search_entry.set_text("")

    def _on_search_activate(self, *args):
        """
        Called when the user does a search.
        """

        # Sets the correct mode
        self.set_mode_movies()
        self.mode_combo.set_active(MODES.index(MODE_MOVIES))

        query = self.search_entry.get_text()
        self.current_movies = {}
        self.background_task(self.pycavane.search_title,
                    self.show_search, query,
                    status_message="Searching movies with title %s..." % query)

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
        cache_dir_button = self.builder.get_object("cachedirButton")
        cache_dir_button.set_filename(self.config.get_key("cache_dir"))

        player_cmd.set_text(self.config.get_key("player_command"))
        self.settings_dialog.run()
        self.settings_dialog.hide()

    def _on_save_settings(self, *args):
        """
        Saves the settings to the disk.
        """

        player_cmd = self.builder.get_object("playerCommandEntry").get_text()
        cache_dir_button = self.builder.get_object("cachedirButton")
        cache_dir = cache_dir_button.get_filename()

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
        marks = self.config.get_key("marks")

        self.file_model.append((ICON_FOLDER, ".."))

        for _, episode_number, episode_name in episodes:
            try:
                episode_name = "%.2d - %s" % (int(episode_number), episode_name)
            except ValueError:
                episode_name = "%s - %s" % (episode_number, episode_name)


            icon = ICON_FILE_MOVIE
            if episode_name in marks:
                icon = ICON_FILE_MOVIE_MARK

            self.file_model.append((icon, episode_name))

    @unfreeze
    def show_search(self, search_result):
        """
        Fills the file viewer with the movies from the search results.
        """

        self.file_model.clear()
        marks = self.config.get_key("marks")

        search_list, maybe_meant = search_result

        if maybe_meant:
            self.set_status_message("Maybe you meant: %s" % maybe_meant)

        if not search_list:
            return

        for result_id, result_name, is_movie in search_list:
            if is_movie:
                icon = ICON_FILE_MOVIE
                if result_name in marks:
                    icon = ICON_FILE_MOVIE_MARK

                self.current_movies[result_name] = result_id
                self.file_model.append((icon, result_name))

    def open_seasson(self, seasson_text):
        """
        Fills the file viewer with the episodes from the seasson.
        """

        show = self.current_show
        self.current_seasson = seasson_text

        self.path_label.set_text(show + " / " + self.current_seasson)

        self.background_task(self.pycavane.episodes_by_season,
                        self.show_episodes, show, seasson_text)

    def open_show(self, episode_text, file_path=None, download_only=False):
        """
        Starts the download of the given episode.
        """

        if episode_text == "..":
            self.background_task(self.pycavane.seasson_by_show,
                           self.show_seassons, self.current_show)
            return

        selected_episode = episode_text.split(" - ", 1)[1]
        show = self.current_show
        seasson = self.current_seasson

        for episode in self.pycavane.episodes_by_season(show, seasson):
            if episode[2] == selected_episode:
                episode_found = episode
                break

        self.background_task(self.download_file, self._on_close_player,
                             episode_found, file_path=file_path,
                             download_only=download_only)

    def open_movie(self, movie_text, file_path=None, download_only=False):
        """
        Starts the download of the given movie.
        """

        movie = (self.current_movies[movie_text], movie_text)
        self.background_task(self.download_file, self._on_close_player,
                             movie, is_movie=True, file_path=file_path,
                             download_only=download_only)

    @unfreeze
    def _on_close_player(self, *args):
        """
        Called when the user closes the player.
        """

        # Nothing to do yet
        pass

    def download_file(self, to_download, is_movie=False,
                      file_path=None, download_only=False):
        """
        Given an resource to download (movie or episode), downloads
        the subtitles, starts downloading the file and starts the player.
        If the resource it's a movie then is_movie has to be True.
        """

        link = self.pycavane.get_direct_links(to_download, host="megaupload",
                                              movie=is_movie)

        if link:
            link = link[1]
        else:
            raise Exception("Not download source found")

        if file_path:
            cache_dir = file_path
        else:
            cache_dir = self.config.get_key("cache_dir")

        megafile = MegaFile(link, cache_dir, self._on_download_error)
        filename = megafile.cache_file

        # Download the subtitle if it exists
        try:
            self.set_status_message("Downloading subtitles...")
            subs_filename = filename.split(".mp4", 1)[0]
            self.pycavane.get_subtitle(to_download, filename=subs_filename,
                                       movie=is_movie)
        except:
            self.set_status_message("Not subtitles found")

        megafile.start()

        self.waiting_time = 45
        gobject.timeout_add_seconds(1, self.update_waiting_message)

        time.sleep(45)  # Megaupload's 45

        file_exists = False

        # Wait until the file exists
        while not file_exists and not self.download_error:
            self.set_status_message("A few seconds left...")
            file_exists = os.path.exists(filename)
            time.sleep(2)

        if self.download_error:
            return

        if download_only:
            status_message = "Downloading: %s"
        else:
            status_message = "Now playing: %s"

        if is_movie:
            self.set_status_message(status_message % to_download[1])
        else:
            self.set_status_message(status_message % to_download[2])

        if download_only:
            while megafile.running:
                time.sleep(5)
        else:
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

    def _on_download_error(self, error):
        """
        Called if the megaupload file has an error.
        """

        self._unfreeze()
        self.set_status_message("Download error: Limit Exceeded")
        self.download_error = True

    def set_mode_shows(self, *args):
        """
        Sets the current mode to shows.
        """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.path_label.set_text("")
        self.name_model.clear()
        self.background_task(self.pycavane.get_shows, self.show_shows,
                             status_message="Obtaining shows list")

    def set_mode_movies(self):
        """
        Sets the current mode to movies.
        """

        self.name_model.clear()
        self.search_entry.grab_focus()
        self.sidebar.hide()
        self.path_label.set_text("")

    def set_mode_favorites(self):
        """
        Sets the current mode to favorites.
        """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.path_label.set_text("")
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


def get_selected_text(view, text_column=0):
    """
    Returns the string of the selected item on the view.
    """

    selection = view.get_selection()
    model, iteration = selection.get_selected()
    selected_text = model.get_value(iteration, text_column)

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

    gui_file = "gui.glade"
    config_file = os.path.expanduser("~") + os.sep + ".guicavane.conf"
    Guicavane(gui_file, config_file)

    if sys.platform == 'win32':
        gobject.threads_init()
    else:
        gtk.gdk.threads_init()

    gtk.main()

if __name__ == "__main__":
    main()
