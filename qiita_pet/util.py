r"""
Util functions (:mod: `qiita_pet.util`)
======================================

..currentmodule:: qiita_pet.util

This module provides different util functions for qiita_pet.

Methods
-------

..autosummary::
    :toctree: generated/

    clean_str
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def linkify(link_template, item):
    """Formats a strings into a URL using string replacement

    Paramters
    ---------
    link_template : str
        The template for the URL.
    item : list or tuple of str
        The strings that will be inserted into the template
    """
    return link_template.format(*item)


def clean_str(item):
    """Converts input to string and replaces spaces with underscores

    Parameters
    ----------
    item : anything convertable to string
        item to convert and clean

    Returns
    -------
    str
        cleaned string
    """
    return str(item).replace(" ", "_").replace(":", "")
