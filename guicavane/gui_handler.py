#!/usr/bin/env python
# coding: utf-8

"""
Gui Handler. Module that takes care of the interface events.
"""

import os
import gtk
import urllib
import webbrowser
from unicodedata import normalize

import pycavane
from constants import *
from player import Player
from config import Config
from settings import Settings
from threadrunner import GtkThreadRunner


class GUIHandler:
    """
    Main class, loads the gui and handles all events.
    """

    def __init__(self):
        """
        Creates the main window.
        """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(MAIN_GUI_FILE)
        self.builder.connect_signals(self)

        # Config
        self.config = Config()

        # Settings window
        self.settings = Settings(self.config)

        # Loading the API
        cache_dir = self.config.get_key("cache_dir")
        if cache_dir[-1] == os.sep:
            cache_dir = cache_dir[:-1]
        self.pycavane = pycavane.Pycavane(cache_dir=cache_dir)

        # Load the player
        self.player = Player(self, self.config, self.on_player_error)

        # Attributes
        self.current_show = None
        self.current_seasson = None
        self.current_movies = {}

        # Getting the used widgets
        self.main_window = self.builder.get_object("mainWindow")
        self.statusbar_label = self.builder.get_object("statusbarLabel")
        self.statusbar_progress = self.builder.get_object("statusbarProgress")
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
        self.info_window = self.builder.get_object("infoWindow")
        self.info_title = self.builder.get_object("infoTitle")
        self.info_label = self.builder.get_object("infoLabel")
        self.info_image = self.builder.get_object("infoImage")

        # Creating a new filter model to allow the user filter the
        # shows and movies by typing on an entry box
        self.name_model_filter = self.name_model.filter_new()
        self.name_model_filter.set_visible_func(generic_visible_func,
                                          (self.name_filter, NAME_COLUMN_TEXT))
        self.name_list.set_model(self.name_model_filter)

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

        # Setup the basic stuff
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

    def unfreeze(func):
        """
        Decorator that calls the decorated function and then unfreezes
        the gui so the user can interact with it.
        """

        def decorate(self, *args, **kwargs):
            self._unfreeze()

            args = [self] + list(args)  # func is a method so it needs self
            func(*args, **kwargs)

        return decorate

    def set_status_message(self, message):
        """
        Sets the message shown in the statusbar.
        """

        self.statusbar_label.set_label(message)

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

    def _on_destroy(self, *args):
        """
        Called when the window closes.
        """

        self.save_config()

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

        self.background_task(self.pycavane.seasson_by_show, self.show_seassons,
            selected_text, status_message="Loading show %s..." % selected_text)

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
            if not selected_text.startswith("Temporada") and \
               not selected_text == "..":
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
                  parent=self.main_window,
                  action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
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

    def save_config(self):
        """
        Saves the config to disk.
        """

        self.config.save()

    def mark_selected(self, *args):
        """
        Called when the user clicks on Mark item in the context menu.
        """

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        selected_text = model.get_value(iteration, FILE_VIEW_COLUMN_TEXT)
        model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE_MARK)

        if selected_text not in self.config.get_key("marks"):
            self.config.append_key("marks", selected_text)

    def unmark_selected(self, *args):
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

    def open_in_cuevana(self, *args):
        """
        Open selected episode or movie on cuevana website.
        """

        selected_text = get_selected_text(self.file_viewer,
                                          FILE_VIEW_COLUMN_TEXT)

        if selected_text.count(" - "):  # It's a serie
            link = "http://www.cuevana.tv/series/%s/%s/%s/"
            show = self.current_show
            season = self.current_seasson

            try:
                selected_episode = selected_text.split(" - ", 1)[1]
            except IndexError:
                return

            data = self.pycavane.episode_by_name(selected_episode,
                                                 show, season)
            assert data != None

            show = normalize_string(show)
            episode = normalize_string(data[2])

            webbrowser.open(link % (data[0], show, episode))
        else:
            link = "http://www.cuevana.tv/peliculas/%s/%s/"
            data = self.pycavane.movie_by_name(selected_text)

            print data[1]
            movie = normalize_string(data[1])

            print movie
            webbrowser.open(link % (data[0], movie))

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

        self.settings.show()

    def _on_info_clicked(self, *args):
        """
        Called when click on the context menu info item.
        """

        selected_text = get_selected_text(self.file_viewer,
                                          FILE_VIEW_COLUMN_TEXT)

        if selected_text.startswith("Temporada"):
            return

        try:
            selected_episode = selected_text.split(" - ", 1)[1]
        except IndexError:
            return

        show = self.current_show
        seasson = self.current_seasson

        episode_found = self.pycavane.episode_by_name(selected_episode,
                                                      show, seasson)

        if not episode_found:
            return

        self.background_task(self.pycavane.get_episode_info,
                        self.open_info_window, episode_found)

    def _on_info_window_close(self, *args):
        """
        Called when the info window is closed.
        """

        self.info_window.hide()

    @unfreeze
    def open_info_window(self, info):
        """
        Opens the info window and loads the info.
        """

        title = "%s: %s" % (self.current_show, info[1])
        desc = info[2]
        image_link = info[0]

        self.background_task(self.download_show_image, self.set_info_image,
                             image_link)

        self.info_title.set_label(title)
        self.info_label.set_label(desc)
        self.info_window.show()

    def download_show_image(self, link):
        """
        Downloads the show image from `link`.
        """

        images_dir = self.config.get_key("images_dir")
        show = self.current_show.lower()
        show_file = show.replace(" ", "_") + ".jpg"
        image_path = images_dir + os.sep + show_file

        if not os.path.exists(image_path):
            url_open = urllib.urlopen(link)
            img = open(image_path, "wb")
            img.write(url_open.read())
            img.close()
            url_open.close()

        return image_path

    @unfreeze
    def set_info_image(self, image_path):
        """
        Sets the image of the current episode.
        """

        pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
        case = gtk.gdk.pixbuf_new_from_file(CASE_IMAGE_PATH)

        width = pixbuf.props.width
        height = pixbuf.props.height

        case = case.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        case.composite(pixbuf, 0, 0, width, height, 0, 0, 1.0, 1.0,
                       gtk.gdk.INTERP_HYPER, 255)

        self.info_image.set_from_pixbuf(pixbuf)

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

        episode_found = self.pycavane.episode_by_name(selected_episode,
                                                      show, seasson)

        self.background_task(self.player.play, self.on_player_finish,
                             episode_found, file_path=file_path,
                             download_only=download_only)

    def open_movie(self, movie_text, file_path=None, download_only=False):
        """
        Starts the download of the given movie.
        """

        movie = (self.current_movies[movie_text], movie_text)
        self.background_task(self.player.play, self.on_player_finish,
                             movie, is_movie=True, file_path=file_path,
                             download_only=download_only)

    @unfreeze
    def on_player_finish(self, error):
        """
        Called when the user closes the player.
        """

        print error
        pass

    def on_player_error(self, error):
        """
        Called if the player has an error.
        """

        self._unfreeze()
        self.set_status_message("Download error: Limit Exceeded")

    def set_mode_shows(self, *args):
        """
        Sets the current mode to shows.
        """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.name_filter.set_text("")
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
        self.name_filter.set_text("")

    def set_mode_favorites(self):
        """
        Sets the current mode to favorites.
        """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.path_label.set_text("")
        self.name_filter.set_text("")
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


def normalize_string(string):
    """
    Take a string and return a cleaned string ready to use for cuevana
    """
    repl_list = [(" ", "-"),
                 (".", ""),
                 (",", ""),
                 ("'", ""),
                 ("?", ""),
                 ("$", ""),
                 ("#", ""),
                 ("*", ""),
                 ("!", ""),
                 (":", "")]

    uni_str = unicode(string, "utf-8")
    clean_str = normalize("NFKD", uni_str).encode("ASCII", "ignore").lower()

    for combo in repl_list:
        clean_str = clean_str.replace(combo[0], combo[1])

    return clean_str
