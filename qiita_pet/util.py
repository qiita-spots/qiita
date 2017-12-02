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
from tornado.escape import linkify as tornado_linkify, xhtml_unescape

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

EBI_LINKIFIER = ('<a href="http://www.ebi.ac.uk/ena/data/view/{0}" '
                 'target="_blank">{0}</a>')


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


def convert_text_html(message):
    """Linkify URLs and turn newlines into <br/> for HTML"""
    html = xhtml_unescape(tornado_linkify(message))
    return html.replace('\n', '<br/>')


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
    values = param.values
    ref = Reference(values['reference'])
    result = ["<b>Reference:</b> %s %s" % (ref.name, ref.version)]
    result.extend("<b>%s:</b> %s" % (name, value)
                  for name, value in viewitems(values)
                  if name != 'reference')
    return "<br/>".join(result)


def is_localhost(host):
    """Verifies if the connection is local

    Parameters
    ----------
    host : str
        The requesting host, in general self.request.headers['host']

    Returns
    -------
    bool
        True if local request
    """
    localhost = ('localhost', '127.0.0.1')
    return host.startswith(localhost)


def get_artifact_processing_status(artifact):
    """Gets the processing status of the artifact

    Parameters
    ----------
    artifact : qiita_db.artifact.Artifact
        The artifact to get the processing status

    Returns
    -------
    str, str
        The processing status {'processing', 'failed', 'success',
            'Not processed'}
        A summary of the jobs attached to the artifact
    """
    preprocessing_status = 'Not processed'
    preprocessing_status_msg = []
    for job in artifact.jobs():
        job_status = job.status
        if job_status == 'error':
            if preprocessing_status != 'success':
                preprocessing_status = 'failed'
            preprocessing_status_msg.append(
                "<b>Job %s</b>: failed - %s"
                % (job.id, job.log.msg))
        elif job_status == 'success':
            preprocessing_status = 'success'
        else:
            if preprocessing_status != 'success':
                preprocessing_status = 'processing'
            preprocessing_status_msg.append(
                "<b>Job %s</b>: %s" % (job.id, job_status))

    if not preprocessing_status_msg:
        preprocessing_status_msg = 'Not processed'
    else:
        preprocessing_status_msg = convert_text_html(
            '<br/>'.join(preprocessing_status_msg))

    return preprocessing_status, preprocessing_status_msg


def get_network_nodes_edges(graph, full_access, nodes=None, edges=None):
    nodes = nodes if nodes is not None else []
    edges = edges if edges is not None else []

    # n[0] is the data type: job/artifact/type
    # n[1] is the object
    for n in graph.nodes():
        if n[0] == 'job':
            atype = 'job'
            name = n[1].command.name
        elif n[0] == 'artifact':
            atype = n[1].artifact_type
            if full_access or n[1].visibility == 'public':
                name = '%s\n(%s)' % (n[1].name, n[1].artifact_type)
            else:
                continue
        elif n[0] == 'type':
            atype = 'type'
            name = '%s\n(%s)' % (n[1].name, n[1].type)
        else:
            # this should never happen but let's add it just in case
            raise ValueError('not valid node type: %s' % n[0])
        nodes.append((n[0], atype, n[1].id, name))

    edges = [(n[1].id, m[1].id) for n, m in graph.edges()]

    return nodes, edges
