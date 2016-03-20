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


FILEPATH_TYPE_TO_SHOW_HEAD = ['FASTQ', 'FASTA', 'FASTA_Sanger']
LINES_TO_READ_FOR_HEAD = 10


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
    dict
        The results of the job

    Raises
    ------
    ValueError
        If there is any error gathering the information from the server
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

    # loop over each of the fps/fps_type pairs
    artifact_information = []
    for (fps, fps_type) in fps_info['filepaths']:
        # Step 2: generate HTML summary
        # md5, from http://stackoverflow.com/a/3431838
        with open(fps, "rb") as f:
            hash_md5 = md5()
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        # getting head of the files
        header = []
        if artifact_type in FILEPATH_TYPE_TO_SHOW_HEAD:
            # we need to encapsulate the full for loop because gzip will not
            # raise an error until you try to read
            try:
                with gopen(fps, 'r') as fin:
                    for i, line in enumerate(fin):
                        header.append(line)
                        if i >= LINES_TO_READ_FOR_HEAD:
                            break
            except:
                with open(fps, 'r') as fin:
                    for i, line in enumerate(fin):
                        header.append(line)
                        if i >= LINES_TO_READ_FOR_HEAD:
                            break
        filename = basename(fps)
        artifact_information.append("<h3>%s (%s)</h3>" % (filename, fps_type))
        artifact_information.append("<b>MD5:</b>: %s</br>" %
                                    hash_md5.hexdigest())
        if header:
            artifact_information.append(
                "<p style=\"font-family:'Courier New', Courier, monospace;"
                "font-size:10;\">%s</p><hr/>" % ("<br/>".join(header)))

    of_fp = join(out_dir, "%s.html" % filename)
    of = open(of_fp, 'w')
    of.write('\n'.join(artifact_information))

    # Step 3: add the new file to the artifact using REST api
    reply = qclient.patch(qclient_url, 'add', '/html_summary/',
                          value=of_fp)

    return reply if not return_html else (reply, artifact_information)
