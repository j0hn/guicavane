#!/usr/bin/env python
# coding: utf-8

"""
SList. Serializable List.

Serializable list it's a data type to save a list to disk serializated
or load one.
"""

import os

try:
    import cPickle as pickle
except ImportError:
    import pickle


class SList(object):
    """ Serializable list, holds a list and provides
    methods to save it and load it from disk. """

    def __init__(self, file_path):
        """ Initialization and creation of the file if necessary. """

        self.slist = []
        self.file_path = file_path

        if not os.path.exists(file_path):
            self.save()

        self.load()

    def load(self):
        """ Loads the data from the file. """

        with open(self.file_path) as filehandler:
            try:
                self.slist = pickle.load(filehandler)
            except:
                self.slist = []

    def save(self):
        """ Saves the list to the file. """

        with open(self.file_path, "w") as filehandler:
            pickle.dump(self.slist, filehandler)

    def add(self, value, save=True):
        """ Adds a value to the list if isn't allready in.
        If save it's True, saves the file right after adding. """

        if value not in self.slist:
            self.slist.append(value)

            if save:
                self.save()

    def remove(self, value, save=True):
        """ Removes a value from the list.
        If save it's True, saves the file after removing. """

        if value in self.slist:
            self.slist.remove(value)

            if save:
                self.save()

    def get_all(self):
        """ Returns a the list. """

        return self.slist
