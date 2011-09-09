#!/usr/bin/env python
# coding: utf-8

import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

from Paths import MARKS_FILE


class Marks(object):
    """ Class that handles marks storege and access. """

    def __init__(self):
        """ Initialization and creation of the file if necessary. """

        self.marks = []

        if not os.path.exists(MARKS_FILE):
            self.save()

        self.load()

    def load(self):
        """ Loads the data from the file. """

        with open(MARKS_FILE) as filehandler:
            try:
                self.marks = pickle.load(filehandler)
            except:
                self.marks = []

    def save(self):
        """ Saves the data to the file. """

        with open(MARKS_FILE, "w") as filehandler:
            pickle.dump(self.marks, filehandler)

    def add(self, name):
        """ Adds a mark to the list. Saves the file right after adding. """

        if str(name) not in self.marks:
            self.marks.append(str(name))
            self.save()

    def remove(self, name):
        """ Removes a mark from the list. Saves the file after removing. """

        if str(name) in self.marks:
            self.marks.remove(str(name))
            self.save()

    def get_all(self):
        """ Returns a list with all the marks. """

        return self.marks
