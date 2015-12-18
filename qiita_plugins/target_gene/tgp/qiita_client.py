# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, dirname, abspath
from os import environ
from future import standard_library

import requests

with standard_library.hooks():
    from configparser import ConfigParser


class QiitaClient(object):
    def __init__(self, server_url):
        self._server_url = server_url

        try:
            conf_fp = environ['QP_TARGET_GENE_CONFIG_FP']
        except KeyError:
            conf_fp = join(dirname(abspath(__file__)), 'support_files',
                           'config_file.cfg')

        config = ConfigParser()
        with open(conf_fp, 'U') as conf_file:
            config.readfp(conf_file)

        server_cert = config.get('main', 'SERVER_CERT')
        if not server_cert:
            # The server certificate is not provided, use standard certificate
            # verification methods
            self._verify = True
        else:
            # The server certificate is provided, use it to verify the identity
            # of the server
            self._verify = server_cert

    def _request_retry(self, req, url, **kwargs):
        """Executes a request retrying it 3 times in case of failure

        Parameters
        ----------
        req : function
            The request to execute
        args : tuple
            The request arguments
        kwargs : dict
            The request kwargs

        Returns
        -------
        dict
            The JSON information in the request reply
        """
        url = self._server_url + url
        success = False
        retries = 3
        json_reply = None
        while not success and retries > 0:
            retries -= 1
            r = req(url, verify=self._verify, **kwargs)
            r.close()
            if r.status_code == 200:
                json_reply = r.json()
                break
        return json_reply

    def get(self, url, **kwargs):
        """"""
        return self._request_retry(requests.get, url, **kwargs)

    def post(self, url, **kwargs):
        """"""
        return self._request_retry(requests.post, url, **kwargs)
