#!/usr/bin/env python
# coding: utf-8

"""
utils.

Module that provides some utils functions.
"""

def combobox_get_active_text(combobox):
    """
    Returns the text of the active item of a gtk combobox.
    """

    model = combobox.get_model()
    active = combobox.get_active()

    if active < 0:
        return None

    return model[active][0]
