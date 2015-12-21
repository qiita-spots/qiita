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
    """Client of the Qiita RESTapi

    Parameters
    ----------
    server_url : str
        The url of the Qiita server

    Methods
    -------
    get
    post
    """
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

        # Set up oauth2
        self._client_id = config.get('main', 'CLIENT_ID')
        self._client_secret = config.get('main', 'CLIENT_SECRET')
        self._authenticate_url = "%s/qiita_db/authenticate/" % self._server_url

        # Fetch the access token
        self._fetch_token()

    def _fetch_token(self):
        """Retrieves an access token from the Qiita server

        Raises
        ------
        ValueError
            If the authentication with the Qiita server fails
        """
        data = {'client_id': self._client_id,
                'client_secret': self._client_secret,
                'grant_type': 'client'}
        r = requests.post(self._authenticate_url, verify=self._verify,
                          data=data)
        if r.status_code != 200:
            raise ValueError("Can't authenticate with the Qiita server")
        self._token = r.json()['access_token']

    def _request_oauth2(self, req, *args, **kwargs):
        """Executes a request using OAuth2 authorization

        Parameters
        ----------
        req : function
            The request to execute
        args : tuple
            The request args
        kwargs : dict
            The request kwargs

        Returns
        -------
        requests.Response
            The request response
        """
        if 'headers' in kwargs:
            kwargs['headers']['Authorization'] = 'Bearer %s' % self._token
        else:
            kwargs['headers'] = {'Authorization': 'Bearer %s' % self._token}
        r = req(*args, **kwargs)
        r.close()
        if r.status_code == 400:
            if r.json()['error_description'] == \
                    'Oauth2 error: token has timed out':
                # The token expired - get a new one and re-try the request
                self._fetch_token()
                r = req(*args, **kwargs)
        return r

    def _request_retry(self, req, url, **kwargs):
        """Executes a request retrying it 2 times in case of failure

        Parameters
        ----------
        req : function
            The request to execute
        url : str
            The url to access in the server
        kwargs : dict
            The request kwargs

        Returns
        -------
        dict
            The JSON information in the request response

        Notes
        -----
        After doing some research on the topic, there are multiple ways of
        engineering the number of times a request should be retried (multiple
        sources - most of them on RPC systems). A short summary of those are:
          1. Keep retrying indefinitely
          2. The probability of retrying a request is based on the number of
          retries already done, as well as the cost of a retry
          3. Retry just once

        Number 1 could create an infinite loop. Number 2 is too complex and
        the cost of retrying depends on the actual work that we are currently
        doing (which is unknown to the current function). We thus decided to
        implement 3, which is simple and allows to overcome simple
        communication problems.
        """
        url = self._server_url + url
        retries = 2
        json_reply = None
        while retries > 0:
            retries -= 1
            r = self._request_oauth2(req, url, verify=self._verify, **kwargs)
            r.close()
            if r.status_code == 200:
                json_reply = r.json()
                break
        return json_reply

    def get(self, url, **kwargs):
        """Execute a get against the Qiita server

        Parameters
        ----------
        url : str
            The url to access in the server
        kwargs : dict
            The request kwargs

        Returns
        -------
        dict
            The JSON response from the server
        """
        return self._request_retry(requests.get, url, **kwargs)

    def post(self, url, **kwargs):
        """Execute a post against the Qiita server

        Parameters
        ----------
        url : str
            The url to access in the server
        kwargs : dict
            The request kwargs

        Returns
        -------
        dict
            The JSON response from the server
        """
        return self._request_retry(requests.post, url, **kwargs)
