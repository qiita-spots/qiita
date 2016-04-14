# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import time
import requests
import threading
from json import dumps

JOB_COMPLETED = False


def heartbeat(qclient, url):
    """Send the heartbeat calls to the server

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    url : str
        The url to issue the heartbeat
    """
    while not JOB_COMPLETED:
        json_reply = qclient.post(url, data='')
        if not json_reply or not json_reply['success']:
            # The server did not accept our heartbeat - stop doing it
            break
        # Perform the heartbeat every 5 seconds
        time.sleep(5)


def format_payload(success, error_msg=None, artifacts_info=None):
    """Generates the payload dictionary for the job

    Parameters
    ----------
    success : bool
        Whether if the job completed successfully or not
    error_msg : str, optional
        If `success` is False, ther error message to include in the optional.
        If `success` is True, it is ignored
    artifacts_info : list of (str, str, list of (str, str))
        For each artifact that needs to be created, the command output name,
        the artifact type and the list of files attached to the artifact.

    Returns
    -------
    dict
        Format:
        {'success': bool,
         'error': str,
         'artifacts': dict of {str: {'artifact_type': str,
                                     'filepaths': list of (str, str)}}
    """
    if success:
        error_msg = ''
        artifacts = {out_name: {'artifact_type': atype,
                                'filepaths': filepaths}
                     for out_name, atype, filepaths in artifacts_info}
    else:
        artifacts = None

    payload = {'success': success,
               'error': error_msg if not success else '',
               'artifacts': artifacts}
    return payload


class QiitaClient(object):
    """Client of the Qiita RESTapi

    Parameters
    ----------
    server_url : str
        The url of the Qiita server
    client_id : str
        The client id to conenct to the Qiita server
    client_secret : str
        The client secret id to connect to the Qiita server
    server_cert : str, optional
        The server certificate, in case that it is not verified


    Methods
    -------
    get
    post
    """
    def __init__(self, server_url, client_id, client_secret, server_cert=None):
        self._server_url = server_url

        # The attribute self._verify is used to provide the parameter `verify`
        # to the get/post requests. According to their documentation (link:
        # http://docs.python-requests.org/en/latest/user/
        # advanced/#ssl-cert-verification ) verify can be a boolean indicating
        # if certificate verification should be performed or not, or a
        # string with the path to the certificate file that needs to be used
        # to verify the identity of the server.
        # We are setting this attribute at __init__ time so we can avoid
        # executing this if statement for each request issued.
        if not server_cert:
            # The server certificate is not provided, use standard certificate
            # verification methods
            self._verify = True
        else:
            # The server certificate is provided, use it to verify the identity
            # of the server
            self._verify = server_cert

        # Set up oauth2
        self._client_id = client_id
        self._client_secret = client_secret
        self._authenticate_url = "%s/qiita_db/authenticate/" % self._server_url

        # Fetch the access token
        print type(requests), self._verify
        print dir(requests)
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
        """Execute a get request against the Qiita server

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
        """Execute a post request against the Qiita server

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

    def patch(self, url, op, path, value=None, from_p=None, **kwargs):
        """Executes a patch request against the Qiita server

        The PATCH request is performed using the JSON PATCH specification [1]_.

        Parameters
        ----------
        url : str
            The url to access in the server
        op : str, {'add', 'remove', 'replace', 'move', 'copy', 'test'}
            The operation to perform in the PATCH request
        path : str
            The target location within the endpoint in which the operation
            should be performed
        value : str, optional
            If `op in ['add', 'replace', 'test']`, the new value for the given
            path
        from_p : str, optional
            If `op in ['move', 'copy']`, the original path
        kwargs : dict
            The request kwargs

        Raises
        ------
        ValueError
            If `op` has one of the values ['add', 'replace', 'test'] and
            `value` is None
            If `op` has one of the values ['move', 'copy'] and `from_p` is None

        References
        ----------
        .. [1] JSON PATCH spec: https://tools.ietf.org/html/rfc6902
        """
        if op in ['add', 'replace', 'test'] and value is None:
            raise ValueError(
                "Operation '%s' requires the paramater 'value'" % op)
        if op in ['move', 'copy'] and from_p is None:
            raise ValueError(
                "Operation '%s' requires the parameter 'from_p'" % op)

        data = {'op': op, 'path': path}
        if value is not None:
            data['value'] = value
        if from_p is not None:
            data['from'] = from_p

        # Add the parameter 'data' to kwargs. Note that if it already existed
        # it is ok to overwrite given that otherwise the call will fail and
        # we made sure that data is correctly formatted here
        kwargs['data'] = data

        return self._request_retry(requests.patch, url, **kwargs)

    # The functions are shortcuts for common functionality that all plugins
    # need to implement.

    def start_heartbeat(self, job_id):
        """Create and start a thread that would send heartbeats to the server

        Parameters
        ----------
        job_id : str
            The job id
        """
        url = "/qiita_db/jobs/%s/heartbeat/" % job_id
        heartbeat_thread = threading.Thread(target=heartbeat, args=(self, url))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def get_job_info(self, job_id):
        """Retrieve the job information from the server

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        dict
            The JSON response from the server with the job information
        """
        return self.get("/qiita_db/jobs/%s" % job_id)

    def update_job_step(self, job_id, new_step):
        """Updates the current step of the job in the server

        Parameters
        ----------
        jon_id : str
            The job id
        new_step : str
            The new step
        """
        json_payload = dumps({'step': new_step})
        self.post("/qiita_db/jobs/%s/step/" % job_id, data=json_payload)

    def complete_job(self, job_id, payload):
        """Stops the heartbeat thread and send the job results to the server

        Parameters
        ----------
        job_id : str
            The job id
        payload : dict
            The job's results

        See Also
        --------
        format_payload
        """
        # Stop the heartbeat thread
        global JOB_COMPLETED
        JOB_COMPLETED = True
        # Create the URL where we have to post the results
        json_payload = dumps(payload)
        self.post("/qiita_db/jobs/%s/complete/" % job_id, data=json_payload)
