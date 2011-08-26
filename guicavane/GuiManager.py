#!/usr/bin/env python
# coding: utf-8

"""
GuiManager. Takes care of the gui events.
"""

import os
import gtk
import urllib

import pycavane
from Constants import *
from threadrunner import GtkThreadRunner


class GuiManager(object):
    """ Main class, loads the gui and handles all events. """

    def __init__(self):
        """ Creates the main window. """

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(MAIN_GUI_FILE)
        self.builder.connect_signals(self)

        # Getting the used widgets
        widgets = ["main_window", "statusbar_label", "progress_box",
                   "progress", "progress_label", "name_filter",
                   "name_filter_clear", "name_list", "file_viewer",
                   "mode_combo", "search_entry", "search_button",
                   "search_clear", "sidebar_vbox", "path_label", "info_window",
                   "info_title", "info_label", "info_image"]

        for widget in widgets:
            setattr(self, widget, self.builder.get_object(widget))

        # Now we show the window
        self.main_window.show_all()

    def freeze(self, status_message="Loading..."):
        """ Freezes the gui so the user can't interact with it. """

        self.main_window.set_sensitive(False)

    def unfreeze(self):
        """ Sets the widgets to be usable. """

        self.main_window.set_sensitive(True)
        self.set_status_message("")

    def set_status_message(self, message):
        """ Sets the message shown in the statusbar.  """

        self.statusbar_label.set_label(message)

    def _on_destroy(self, *args):
        """ Called when the window closes.  """

        #self.save_config()

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

        self.background_task(self.pycavane.add_favorite,
                             self.on_finish_favorite, selected, False)

    def _on_name_remove_favorite(self, *args):
        """
        Removes the selected show from favorites.
        """

        selected = get_selected_text(self.name_list, NAME_COLUMN_TEXT)
        if selected in self.config.get_key("favorites"):
            self.config.remove_key("favorites", selected)
            self.set_mode_favorites()

        self.background_task(self.pycavane.del_favorite,
                             self.on_finish_favorite, selected, False)

    def on_finish_favorite(self, *args):
        pass

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

    def _on_name_key_press(self, treeview, event):
        """
        Called when the users presses a key on the name filter list.
        """

        acceptedchars = map(chr, range(97, 123)) + map(chr, range(65, 91)) \
                        + ['0','1','2','3','4','5','6','7','8','9']

        key = gtk.gdk.keyval_name(event.keyval)
        if key in acceptedchars:
            self.name_filter.set_text(key)
            self.name_filter.grab_focus()
            self.name_filter.set_position(len(self.name_filter.get_text()))

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

        self.marks.add(selected_text)

    def unmark_selected(self, *args):
        """
        Called when the user clicks on Mark item in the context menu.
        """

        marks = self.marks.get_all()

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        selected_text = model.get_value(iteration, FILE_VIEW_COLUMN_TEXT)

        if selected_text in marks:
            model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE)
            self.marks.remove(selected_text)

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
        self.background_task(self.search_movies,
                    self.show_search, query,
                    status_message="Searching movies with title %s..." % query)

    def search_movies(self, query):
        search = self.pycavane.search_title(query)
        next_movies_pages_search = 3

        movies = search[0]
        for i in range(1, next_movies_pages_search + 1):
            next_movies = self.pycavane.get_next_movies(i)
            next_matched = [x for x in next_movies if \
                            x[1].lower().count(query.lower()) > 0]
            movies += next_matched


        return (movies, search[1])

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

    def open_info_window(self, info):
        """
        Opens the info window and loads the info.
        """

        title = "%s: %s" % (self.current_show, info[1])
        desc = info[2]
        image_link = info[0]

        empty_case = gtk.gdk.pixbuf_new_from_file(IMAGE_CASE_EMPTY)
        self.info_image.set_from_pixbuf(empty_case)

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

    def set_info_image(self, image_path):
        """
        Sets the image of the current episode.
        """

        pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
        case = gtk.gdk.pixbuf_new_from_file(IMAGE_CASE)

        width = pixbuf.props.width
        height = pixbuf.props.height

        case = case.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        case.composite(pixbuf, 0, 0, width, height, 0, 0, 1.0, 1.0,
                       gtk.gdk.INTERP_HYPER, 255)

        self.info_image.set_from_pixbuf(pixbuf)

    def show_shows(self, shows):
        """
        Adds all the shows to the list.
        """

        self.file_model.clear()

        for _, show_name in shows:
            self.name_model.append([show_name])

    def show_seassons(self, seassons):
        """
        Fills the file viewer with the seassons.
        """

        self.file_model.clear()

        for _, seasson_name in seassons:
            self.file_model.append((ICON_FOLDER, seasson_name))

    def show_episodes(self, episodes):
        """
        Fills the file viewer with the episodes.
        """

        self.file_model.clear()
        marks = self.marks.get_all()

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

    def show_search(self, search_result):
        """
        Fills the file viewer with the movies from the search results.
        """

        self.file_model.clear()
        marks = self.marks.get_all()

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

    def on_player_finish(self, error):
        """
        Called when the user closes the player.
        """

        self._unfreeze()

        if error:
            self.set_status_message(str(error))

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

    def update_favorites(self, favorites):
        for fav in favorites:
            if fav not in self.config.get_key("favorites"):
                self.config.append_key("favorites", fav)

        if self.get_mode() == MODE_FAVORITES:
            self.set_mode_favorites()

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
