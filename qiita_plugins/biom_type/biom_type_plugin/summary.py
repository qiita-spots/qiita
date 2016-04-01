# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


from biom import load_table
from urllib import quote
from base64 import b64encode
from os.path import join, basename
import numpy as np
from StringIO import StringIO

import seaborn as sns
from qiita_client import format_payload


def generate_html_summary(qclient, job_id, parameters, out_dir,
                          return_html=False):
    """Generates the HTML summary of a BIOM artifact

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
    dict(, [str])
        The results of the job and if return_html is True an array of str

    Raises
    ------
    ValueError
        If there is any error gathering the information from the server
    """
    # Step 1: gather file information from qiita using REST api
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

    # if we get to this point of the code we are sure that this is a biom file
    # and that it only has one element
    fps, fps_type = fps_info['filepaths'][0]

    # Step 2: generate HTML summary
    # Modified from https://goo.gl/cUVHgB
    biom = load_table(fps)
    num_features, num_samples = biom.shape

    sample_counts = []
    for count_vector, id_, _ in biom.iter(axis='sample'):
        sample_counts.append(float(count_vector.sum()))
    sample_counts = np.asarray(sample_counts)

    sample_count_summary = {
        'Minimum count': sample_counts.min(),
        'Maximum count': sample_counts.max(),
        'Mean count': np.mean(sample_counts),
        'Median count': np.median(sample_counts),
    }

    ax = sns.distplot(sample_counts)
    ax.set_xlabel("Number of sequences per sample")
    ax.set_ylabel("Frequency")
    plot = ax.get_figure()
    sc_plot = StringIO()
    plot.savefig(sc_plot, format='png')
    sc_plot.seek(0)

    uri = 'data:image/png;base64,' + quote(b64encode(sc_plot.buf))
    artifact_information = [
        "<b>Number of samples:</b> %d<br/>" % num_samples,
        "<b>Number of features:</b> %d<br/>" % num_features,
        ("<b>Minimum count:</b> %d<br/>" %
         sample_count_summary['Minimum count']),
        ("<b>Maximum count:</b> %d<br/>" %
         sample_count_summary['Maximum count']),
        ("<b>Median count:</b> %d<br/>" %
         sample_count_summary['Median count']),
        ("<b>Mean count:</b> %d<br/>" %
         sample_count_summary['Mean count']),
        '<br/><hr/><br/>',
        '<img src = "%s"/>' % uri
    ]

    of_fp = join(out_dir, "%s.html" % basename(fps))
    with open(of_fp, 'w') as of:
        of.write('\n'.join(artifact_information))

    # Step 3: add the new file to the artifact using REST api
    reply = qclient.patch(qclient_url, 'add', '/html_summary/', value=of_fp)

    payload = format_payload(
        success=reply['success'], error_msg=reply['error'], artifacts_info=[])

    return payload if not return_html else (payload, artifact_information)
