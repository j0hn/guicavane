#!/usr/bin/env python
# coding: utf-8

"""
GuiManager. Takes care of the gui events.
"""

import os
import gtk
import urllib
import webbrowser

import pycavane
from Constants import *
from Marks import Marks
from Config import Config
from Player import Player
from Settings import SettingsDialog
from ThreadRunner import GtkThreadRunner


class GuiManager(object):
    """ Main class, loads the gui and handles all events. """

    def __init__(self):
        """ Creates the main window. """

        # Attributes
        self.current_show = None
        self.current_season = None

        # Config, Marks and Settings
        self.config = Config()
        self.marks = Marks()
        self.settings_dialog = SettingsDialog(self.config)

        # Gtk builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(MAIN_GUI_FILE)
        self.builder.connect_signals(self)

        # Getting the used widgets
        glade_objects = [
            "main_window", "statusbar_label", "progress_box", "progress",
            "progress_label", "name_filter", "name_filter_clear", "name_list",
            "name_list_model", "file_viewer", "file_viewer_model",
            "mode_combo", "search_entry", "search_button", "search_clear",
            "sidebar", "sidebar_vbox", "path_label", "info_window",
            "info_title", "info_label", "info_image", "file_viewer_menu",
            "error_label", "error_dialog", "header_hbox", "main_hpaned",
            "about_dialog",
        ]

        for glade_object in glade_objects:
            setattr(self, glade_object, self.builder.get_object(glade_object))

        # Set up the filter for the show list
        self.name_list_model_filter = self.name_list_model.filter_new()
        self.name_list_model_filter.set_visible_func(generic_visible_func,
            (self.name_filter, NAME_LIST_COLUMN_TEXT))
        self.name_list.set_model(self.name_list_model_filter)

        # Now we show the window
        self.main_window.show_all()

        # Start on last mode
        try:
            last_mode = self.config.get_key("last_mode")
            getattr(self, "set_mode_%s" % last_mode.lower())()
            self.mode_combo.set_active(MODES.index(last_mode))
        except:
            self.set_mode_shows()

    def freeze(self, status_message="Loading..."):
        """ Freezes the gui so the user can't interact with it. """

        self.header_hbox.set_sensitive(False)
        self.main_hpaned.set_sensitive(False)
        self.set_status_message(status_message)

    def unfreeze(self):
        """ Sets the widgets to be usable. """

        self.header_hbox.set_sensitive(True)
        self.main_hpaned.set_sensitive(True)
        self.set_status_message("")

    def background_task(self, func, callback, *args, **kwargs):
        """
        Freezes the gui, starts a thread with func.
        When it's done, unfreezes the gui and calls callback with the result.

        The results it's a tuple (is_error, result) with a boolean if
        an error has ocurred and the exception, or the result if there
        was no errors.
        """

        status_message = "Loading..."

        if "status_message" in kwargs:
            status_message = kwargs["status_message"]
            del kwargs["status_message"]

        if "unfreeze" in kwargs and not kwargs["unfreeze"]:
            real_callback = callback
            del kwargs["unfreeze"]
        else:

            def real_callback(result):
                self.unfreeze()
                callback(result)

        self.freeze(status_message)
        GtkThreadRunner(real_callback, func, *args, **kwargs)

    def set_status_message(self, message):
        """ Sets the message shown in the statusbar.  """

        self.statusbar_label.set_label(message)

    def set_mode_shows(self, *args):
        """ Sets the current mode to shows. """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.name_filter.set_text("")
        self.path_label.set_text("")
        self.name_list_model.clear()
        self.background_task(pycavane.api.Show.search, self.display_shows,
                             status_message="Obtaining shows list")

    def set_mode_movies(self):
        """ Sets the current mode to movies. """

        self.name_list_model.clear()
        self.search_entry.grab_focus()
        self.sidebar.hide()
        self.path_label.set_text("")
        self.name_filter.set_text("")

    def set_mode_favorites(self):
        """ Sets the current mode to favorites. """

        self.sidebar.show()
        self.search_entry.set_text("")
        self.path_label.set_text("")
        self.name_filter.set_text("")
        self.name_list_model.clear()
        for favorite in self.config.get_key("favorites"):
            show = pycavane.api.Show.search(favorite).next()
            self.name_list_model.append([show.name, show])

    def update_favorites(self, favorites):
        for fav in favorites:
            if fav not in self.config.get_key("favorites"):
                self.config.append_key("favorites", fav)

        if self.get_mode() == MODE_FAVORITES:
            self.set_mode_favorites()

    def get_mode(self):
        """ Returns the current mode. i.e the value of the mode combobox.
        The result will be the constant MODE_* (see constants definitions). """

        model = self.mode_combo.get_model()
        active = self.mode_combo.get_active()
        mode_text = model[active][0]

        # Poscondition
        assert mode_text in MODES

        return mode_text

    def report_error(self, message):
        """ Shows up an error dialog to the user. """

        self.error_label.set_label(message)
        self.error_dialog.show_all()
        self.set_status_message("")
        self.unfreeze()

    def display_shows(self, (is_error, result)):
        """ Displays the shows. """

        self.name_list_model.clear()
        self.file_viewer_model.clear()

        if is_error:
            message = "Problem fetching shows, "
            message += "please try again in a few minutes."
            self.report_error(message)
            return

        for show in result:
            self.name_list_model.append([show.name, show])

    def display_seasons(self, (is_error, result)):
        """ Fills the file viewer with the seasons. """

        if is_error:
            message = "Problem fetching seasons, "
            message = "please try again in a few minutes."
            self.report_error(message)
            return

        self.file_viewer_model.clear()

        for season in result:
            self.file_viewer_model.append([ICON_FOLDER, season.name, season])

    def display_episodes(self, (is_error, result)):
        """ Fills the file viewer with the episodes. """

        if is_error:
            message = "Problem fetching episodes, "
            message = "please try again in a few minutes."
            self.report_error(message)
            return

        self.file_viewer_model.clear()
        marks = self.marks.get_all()

        # Add the 'up' folder
        self.file_viewer_model.append([ICON_FOLDER, "..", None])

        for episode in result:
            episode_name = "%s - %s" % (episode.number, episode.name)

            icon = ICON_FILE_MOVIE
            if episode.id in marks:
                icon = ICON_FILE_MOVIE_MARK

            self.file_viewer_model.append([icon, episode_name, episode])

    def display_movies(self, (is_error, result)):
        """ Fills the file viewer with the movies from the search results. """

        if is_error:
            message = "Problem fetching movies, "
            message = "please try again in a few minutes."
            self.report_error(message)
            return

        self.file_viewer_model.clear()

        for movie in result:
            name = movie.name
            icon = ICON_FILE_MOVIE
            self.file_viewer_model.append([icon, name, movie])

    # ================================
    # =         CALLBACKS            =
    # ================================

    def _on_destroy(self, *args):
        """ Called when the window closes.  """

        #self.save_config()

        # We kill gtk
        gtk.main_quit()

    def _on_mode_change(self, *args):
        """ Called when the mode combobox changes value. """

        last_mode = self.get_mode()
        self.config.set_key("last_mode", last_mode)

        self.file_viewer_model.clear()

        # Call the corresponding set_mode method
        getattr(self, "set_mode_%s" % last_mode.lower())()

    def _on_show_selected(self, tree_view, path, column):
        """ Called when the user selects a show from the name list. """

        self.file_viewer_model.clear()

        model = tree_view.get_model()
        selected_show = model[path][NAME_LIST_COLUMN_OBJECT]

        self.current_show = selected_show
        self.path_label.set_text(selected_show.name)

        self.background_task(pycavane.api.Season.search, self.display_seasons,
                selected_show, status_message="Loading show %s..." % \
                selected_show.name)

    def _on_file_viewer_open(self, widget, path, *args):
        """ Called when the user double clicks on a file
        inside the file viewer. """

        file_object = self.file_viewer_model[path][FILE_VIEW_COLUMN_OBJECT]

        mode = self.get_mode()

        if isinstance(file_object, pycavane.api.Movie):
            Player(self, file_object)
        elif isinstance(file_object, pycavane.api.Season):
            self.current_season = file_object

            self.path_label.set_text("%s / %s" % \
                    (self.current_show.name, self.current_season.name))

            self.background_task(pycavane.api.Episode.search,
                                 self.display_episodes, file_object)
        elif isinstance(file_object, pycavane.api.Episode):
            Player(self, file_object)
        elif file_object == None:
            self.background_task(pycavane.api.Season.search, self.display_seasons,
                self.current_show, status_message="Loading show %s..." % \
                self.current_show.name)

    def _on_name_filter_change(self, *args):
        """ Called when the textbox to filter names changes. """

        self.name_list_model_filter.refilter()

    def _on_name_filter_clear_clicked(self, *args):
        """ Clears the name filter input. """

        self.name_filter.set_text("")

    def _on_name_filter_keypress(self, widget, event):
        """ Called when the user presses a key in the name
        filter. It clears it out if the key is escape. """

        key = gtk.gdk.keyval_name(event.keyval)
        if key == "Escape":
            self.name_filter.set_text("")

    def _on_name_button_press(self, view, event):
        """ Called when the user press any mouse button on the name list. """

        if event.button == 3:  # 3 it's right click
            if self.get_mode() == MODE_FAVORITES:
                popup_menu = self.builder.get_object("name_favorites_menu")
            else:
                popup_menu = self.builder.get_object("name_shows_menu")

            popup_menu.popup(None, None, None, event.button, event.time)

    def _on_add_favorite(self, *args):
        """ Adds the selected show from favorites.  """

        path, _ = self.name_list.get_cursor()
        model = self.name_list.get_model()
        selected = model[path][NAME_LIST_COLUMN_TEXT]

        if selected not in self.config.get_key("favorites"):
            self.config.append_key("favorites", selected)

        #self.background_task(self.pycavane.add_favorite,
        #                     self.on_finish_favorite, selected, False)

    def _on_remove_favorite(self, *args):
        """ Removes the selected show from favorites. """

        path, _ = self.name_list.get_cursor()
        model = self.name_list.get_model()
        selected = model[path][NAME_LIST_COLUMN_TEXT]

        if selected in self.config.get_key("favorites"):
            self.config.remove_key("favorites", selected)
            self.set_mode_favorites()

        #self.background_task(self.pycavane.del_favorite,
        #                     self.on_finish_favorite, selected, False)

    def _on_file_button_press(self, view, event):
        """ Called when the user press any mouse button on the file viewer. """

        if event.button == 3:  # Right button
            path, _ = view.get_cursor()
            model = view.get_model()
            file_object = model[path][FILE_VIEW_COLUMN_OBJECT]

            if isinstance(file_object, pycavane.api.Episode) or \
               isinstance(file_object, pycavane.api.Movie):
                self.file_viewer_menu.popup(None, None, None, event.button, event.time)

    def _on_menu_play_clicked(self, *args):
        """ Called when the user click on the play context menu item. """

        path, _ = self.file_viewer.get_cursor()
        file_object = self.file_viewer_model[path][FILE_VIEW_COLUMN_OBJECT]
        Player(self, file_object)

    def _on_menu_download_only_clicked(self, widget):
        """ Called when the user click on the download only
        context menu item. """

        self._on_menu_download_clicked(widget, download_only=True)

    def _on_menu_download_clicked(self, widget, download_only=False):
        """ Called when the user click on the download and
        play context menu item. """

        chooser = gtk.FileChooserDialog(title="Dowload to...",
                  parent=self.main_window,
                  action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                  gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        last_download_dir = self.config.get_key("last_download_directory")
        chooser.set_current_folder(last_download_dir)
        response = chooser.run()

        if response != gtk.RESPONSE_OK:
            chooser.destroy()
            return

        save_to = chooser.get_filename()
        self.config.set_key("last_download_directory", save_to)
        chooser.destroy()

        path, _ = self.file_viewer.get_cursor()
        file_object = self.file_viewer_model[path][FILE_VIEW_COLUMN_OBJECT]
        Player(self, file_object, save_to, download_only=download_only)

    def _on_name_key_press(self, treeview, event):
        """ Called when the users presses a key on the name filter list. """

        chr_numbers = range(48, 57) + range(65, 91) + range(97, 123)
        acceptedchars = map(chr, chr_numbers)

        key = gtk.gdk.keyval_name(event.keyval)
        if key in acceptedchars:
            self.name_filter.set_text(key)
            self.name_filter.grab_focus()
            self.name_filter.set_position(len(self.name_filter.get_text()))

    def mark_selected(self, *args):
        """ Called when the user clicks on Mark item in the context menu. """

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        episode = model.get_value(iteration, FILE_VIEW_COLUMN_OBJECT)
        model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE_MARK)

        self.marks.add(episode.id)

    def unmark_selected(self, *args):
        """ Called when the user clicks on Mark item in the context menu. """

        marks = self.marks.get_all()

        selection = self.file_viewer.get_selection()
        model, iteration = selection.get_selected()
        episode = model.get_value(iteration, FILE_VIEW_COLUMN_OBJECT)

        if episode.id in marks:
            model.set_value(iteration, FILE_VIEW_COLUMN_PIXBUF, ICON_FILE_MOVIE)
            self.marks.remove(episode.id)

    def open_in_cuevana(self, *args):
        """ Open selected episode or movie on cuevana website. """

        path, _ = self.file_viewer.get_cursor()
        file_object = self.file_viewer_model[path][FILE_VIEW_COLUMN_OBJECT]
        webbrowser.open(file_object.cuevana_url)

    def _on_search_clear_clicked(self, *args):
        """ Clears the search input. """

        self.search_entry.set_text("")

    def _on_search_activate(self, *args):
        """ Called when the user does a search. """

        # Sets the correct mode
        self.set_mode_movies()
        self.mode_combo.set_active(MODES.index(MODE_MOVIES))

        query = self.search_entry.get_text()
        self.background_task(pycavane.api.Movie.search,
                    self.display_movies, query,
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

    def _on_about_clicked(self, *args):
        """ Opens the about dialog. """

        self.about_dialog.run()
        self.about_dialog.hide()

    def _on_open_settings(self, *args):
        """ Called when the user opens the preferences from the menu. """

        self.settings_dialog.show()

    def _on_info_clicked(self, *args):
        """
        Called when click on the context menu info item.
        """

        path, _ = self.file_viewer.get_cursor()
        file_object = self.file_viewer_model[path][FILE_VIEW_COLUMN_OBJECT]

        if isinstance(file_object, pycavane.api.Episode):
            empty_case = gtk.gdk.pixbuf_new_from_file(IMAGE_CASE_EMPTY)
            self.info_image.set_from_pixbuf(empty_case)

            self.background_task(self.download_show_image, self.set_info_image,
                                 file_object)

            full_description = file_object.info["description"] + "\n\n" \
                "<b>Cast:</b> " + ", ".join(file_object.info["cast"]) + "\n" \
                "<b>Genere:</b> " + file_object.info["genere"] + "\n" \
                "<b>Language:</b> " + file_object.info["language"]

            self.info_title.set_label(file_object.info["name"])
            self.info_label.set_label(full_description)
            self.info_window.show()

    def _on_info_window_close(self, *args):
        """ Called when the info window is closed. """

        self.info_window.hide()

    def download_show_image(self, file_object):
        """ Downloads the current show image and returs the path to it. """

        self.unfreeze()

        images_dir = self.config.get_key("images_dir")
        show_name = self.current_show.name.lower()
        show_name = show_name.replace(" ", "_") + ".jpg"
        image_path = os.path.join(images_dir, show_name)

        if not os.path.exists(image_path):
            url_open = urllib.urlopen(file_object.info["image"])
            img = open(image_path, "wb")
            img.write(url_open.read())
            img.close()
            url_open.close()

        return image_path

    def set_info_image(self, (is_error, result)):
        """ Sets the image of the current episode. """

        if is_error:
            self.set_status_message("Problem downloading show image")
            return

        image_path = result

        pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
        case = gtk.gdk.pixbuf_new_from_file(IMAGE_CASE)

        width = pixbuf.props.width
        height = pixbuf.props.height

        case = case.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        case.composite(pixbuf, 0, 0, width, height, 0, 0, 1.0, 1.0,
                       gtk.gdk.INTERP_HYPER, 255)

        self.info_image.set_from_pixbuf(pixbuf)

    def on_player_finish(self, error):
        """
        Called when the user closes the player.
        """

        self._unfreeze()

        if error:
            self.set_status_message(str(error))

    def _on_hide_error_dialog(self, button):
        """ Called when the user closes the error dialog. """
        self.error_dialog.hide()


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
