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


def generate_html_summary(qclient, job_id, parameters, out_dir):
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

    Returns
    -------
    bool, None, str
        Whether the job is successful
        Ignored
        The error message, if not successful

    Raises
    ------
    ValueError
        - If there is any error gathering the information from the server
        - If the artifact is 'Demultiplexed' but it doesn't have a demux file
    """
    # Step 1: gather file information from qiita using REST api
    artifact_id = parameters['input_data']
    qclient_url = "/qiita_db/artifacts/%s/" % artifact_id
    a_info = qclient.get(qclient_url)
    # 1a. getting the file paths
    fps_info = a_info['files']
    # 1.b get the artifact type_info
    artifact_type = a_info['type']

    # we have 2 main cases: Demultiplexed and everything else, splitting on
    # those
    if artifact_type == 'Demultiplexed':
        artifact_information = _summary_demultiplexed(
            artifact_type, fps_info)
        if artifact_information is None:
            raise ValueError("We couldn't find a demux file in your artifact")
    else:
        artifact_information = _summary_not_demultiplexed(
            artifact_type, fps_info)

    of_fp = join(out_dir, "artifact_%d.html" % artifact_id)
    with open(of_fp, 'w') as of:
        of.write('\n'.join(artifact_information))

    # Step 3: add the new file to the artifact using REST api
    success = True
    error_msg = ''
    try:
        qclient.patch(qclient_url, 'add', '/html_summary/', value=of_fp)
    except Exception as e:
        success = False
        error_msg = str(e)

    return success, None, error_msg


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
    for (fps_type, fps) in sorted(filepaths.items()):
        for fp in fps:
            # Step 2: generate HTML summary
            # md5, from http://stackoverflow.com/a/3431838
            with open(fp, "rb") as f:
                hash_md5 = md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            # getting head of the files
            header = []
            if artifact_type not in FILEPATH_TYPE_TO_NOT_SHOW_HEAD:
                # we need to encapsulate the full for loop because gzip will
                # not raise an error until you try to read
                try:
                    with gopen(fp, 'r') as fin:
                        header = [
                            next(fin) for x in xrange(LINES_TO_READ_FOR_HEAD)]
                except IOError:
                    with open(fp, 'r') as fin:
                        header = [
                            next(fin) for x in xrange(LINES_TO_READ_FOR_HEAD)]
            filename = basename(fp)
            artifact_information.append("<h3>%s (%s)</h3>"
                                        % (filename, fps_type))
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
    demux_fp = filepaths.get('preprocessed_demux')
    if demux_fp is None:
        return None

    # At this point demux_fp is a list, but we know it only has 1 element
    demux_fp = demux_fp[0]

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
    plt.xlabel('Sequence Length')
    plt.ylabel('Number of sequences')
    plot = StringIO()
    plt.savefig(plot, format='png')
    plot.seek(0)
    uri = 'data:image/png;base64,' + quote(b64encode(plot.buf))
    artifact_information.append('<img src = "%s"/>' % uri)

    return artifact_information
