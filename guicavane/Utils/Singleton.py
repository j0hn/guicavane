#!/usr/bin/env python
# coding: utf-8

"""
Singleton.

Not really singleton but close taken
from dx https://github.com/dequis/derpbot/blob/master/util.py
"""


class Singleton(object):
    instance = None

    def __init__(self):
        if type(self).instance is not None:
            raise TypeError("Already instantiated, use .get()")

        type(self).instance = self

    @classmethod
    def get(cls):
        return cls.instance or cls()
