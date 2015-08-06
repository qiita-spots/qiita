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
from future.utils import viewitems
from tornado.escape import linkify as tornado_linkify

from qiita_core.util import execute_as_transaction
from qiita_db.reference import Reference


STATUS_STYLER = {
    'sandbox':
        ('glyphicon glyphicon-eye-close', 'glyphicon glyphicon-lock', 'gray'),
    'awaiting_approval':
        ('glyphicon glyphicon-eye-open', 'glyphicon glyphicon-lock', 'peru'),
    'private':
        ('glyphicon glyphicon-eye-open', 'glyphicon glyphicon-lock',
         '#3599FD'),
    'public':
        ('glyphicon glyphicon-eye-open', 'glyphicon glyphicon-globe', 'green')}


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


def make_text_html(message):
    """Linkify URLs and turn newlines into <br/> for HTML"""
    lines = message.split('\n')
    new_text = []
    for line in lines:
        new_text.append(tornado_linkify(line))
    return "<br/>".join(new_text)


@execute_as_transaction
def generate_param_str(param):
    """Generate an html string with the parameter values

    Parameters
    ----------
    param : BaseParameters
        The parameter to generate the str

    Returns
    -------
    str
        The html string with the parameter set values
    """
    ref = Reference(param.reference)
    result = ["<b>Reference:</b> %s %s" % (ref.name, ref.version)]
    result.extend("<b>%s:</b> %s" % (name, value)
                  for name, value in viewitems(param.values)
                  if name != 'reference_id')
    return "<br/>".join(result)
