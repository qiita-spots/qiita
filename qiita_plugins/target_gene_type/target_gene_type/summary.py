# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from hashlib import md5
from gzip import open as gopen
from os.path import basename, join
from urllib import quote
from base64 import b64encode
from StringIO import StringIO

from qiita_ware.demux import stats as demux_stats
import matplotlib.pyplot as plt


FILEPATH_TYPE_TO_NOT_SHOW_HEAD = ['SFF']
LINES_TO_READ_FOR_HEAD = 10


def generate_html_summary(qclient, job_id, parameters, out_dir,
                          return_html=False):
    """Generates the HTML summary of a target gene type artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to validate and create the artifact
    out_dir : str
        The path to the job's output directory
    return_html : bool, optional
        True will return the html str, useful for testing

    Returns
    -------
    dict
        The results of the job

    Raises
    ------
    ValueError
        - If there is any error gathering the information from the server
        - If the artifact is 'Demultiplexed' but it doesn't have a demux file
    """
    # Step 1: gather file information from qiita using REST api
    # 1a. getting the file paths
    artifact_id = parameters['input_data']
    qclient_url = "/qiita_db/artifacts/%s/filepaths/" % artifact_id
    fps_info = qclient.get(qclient_url)
    if not fps_info or not fps_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if fps_info:
            error_msg = error_msg % fps_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    # 1.b get the artifact type_info
    type_info = qclient.get("/qiita_db/artifacts/%s/type/" % artifact_id)
    if not type_info or not type_info['success']:
        error_msg = "Could not get artifact metadata information %s"
        if type_info:
            error_msg = error_msg % type_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    artifact_type = type_info['type']

    # we have 2 main cases: Demultiplexed and everything else, splitting on
    # those
    if artifact_type == 'Demultiplexed':
        artifact_information = _summary_demultiplexed(
            artifact_type, fps_info['filepaths'])
        if artifact_information is None:
            raise ValueError("We couldn't find a demux file in your artifact")
    else:
        artifact_information = _summary_not_demultiplexed(
            artifact_type, fps_info['filepaths'])

    of_fp = join(out_dir, "artifact_%d.html" % artifact_id)
    with open(of_fp, 'w') as of:
        of.write('\n'.join(artifact_information))

    # Step 3: add the new file to the artifact using REST api
    reply = qclient.patch(qclient_url, 'add', '/html_summary/',
                          value=of_fp)

    return reply if not return_html else (reply, artifact_information)


def _summary_not_demultiplexed(artifact_type, filepaths):
    """Generates the HTML summary for non Demultiplexed artifacts

    Parameters
    ----------
    artifact_type : str
        The artifact type
    filepaths : [(str, str)]
        A list of string pairs where the first element is the filepath and the
        second is the filepath type

    Returns
    -------
    list
        A list of strings with the html summary
    """
    # loop over each of the fps/fps_type pairs
    artifact_information = []
    for (fps, fps_type) in filepaths:
        # Step 2: generate HTML summary
        # md5, from http://stackoverflow.com/a/3431838
        with open(fps, "rb") as f:
            hash_md5 = md5()
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        # getting head of the files
        header = []
        if artifact_type not in FILEPATH_TYPE_TO_NOT_SHOW_HEAD:
            # we need to encapsulate the full for loop because gzip will not
            # raise an error until you try to read
            try:
                with gopen(fps, 'r') as fin:
                    header = [
                        next(fin) for x in xrange(LINES_TO_READ_FOR_HEAD)]
            except IOError:
                with open(fps, 'r') as fin:
                    header = [
                        next(fin) for x in xrange(LINES_TO_READ_FOR_HEAD)]
        filename = basename(fps)
        artifact_information.append("<h3>%s (%s)</h3>" % (filename, fps_type))
        artifact_information.append("<b>MD5:</b>: %s</br>" %
                                    hash_md5.hexdigest())
        if header:
            artifact_information.append(
                "<p style=\"font-family:'Courier New', Courier, monospace;"
                "font-size:10;\">%s</p><hr/>" % ("<br/>".join(header)))

    return artifact_information


def _summary_demultiplexed(artifact_type, filepaths):
    """Generates the HTML summary for Demultiplexed artifacts

    Parameters
    ----------
    artifact_type : str
        The artifact type
    filepaths : [(str, str)]
        A list of string pairs where the first element is the filepath and the
        second is the filepath type

    Returns
    -------
    list
        A list of strings with the html summary
    """
    # loop over each of the fps/fps_type pairs to find the demux_fp
    demux_fp = None
    for (fps, fps_type) in filepaths:
        if fps_type == 'preprocessed_demux':
            demux_fp = fps
            break
    if demux_fp is None:
        return None

    # generating html summary
    artifact_information = []
    sn, smax, smin, smean, sstd, smedian, shist, shist_edge = demux_stats(
        demux_fp)
    artifact_information.append("<h3>Features</h3>")
    artifact_information.append('<b>Total</b>: %d' % sn)
    artifact_information.append("<br/>")
    artifact_information.append('<b>Max</b>: %d' % smax)
    artifact_information.append("<br/>")
    artifact_information.append('<b>Mean</b>: %d' % smean)
    artifact_information.append("<br/>")
    artifact_information.append('<b>Standard deviation</b>: %d' % sstd)
    artifact_information.append("<br/>")
    artifact_information.append('<b>Median</b>: %d' % smedian)
    artifact_information.append("<br/>")

    # taken from http://stackoverflow.com/a/9141911
    plt.bar(shist_edge[:-1], shist, width=1)
    plt.xlim(min(shist_edge), max(shist_edge))
    plot = StringIO()
    plt.savefig(plot, format='png')
    plot.seek(0)
    uri = 'data:image/png;base64,' + quote(b64encode(plot.buf))
    artifact_information.append('<img src = "%s"/>' % uri)

    return artifact_information
