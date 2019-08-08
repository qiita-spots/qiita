import functools
import urllib.parse as urllib_parse
from tornado import escape
from tornado.concurrent import future_set_result_unless_cancelled
from tornado.stack_context import wrap
from tornado.auth import (AuthError, OAuth2Mixin, _auth_return_future)


class GlobusOAuth2Mixin(OAuth2Mixin):
    _OAUTH_AUTHORIZE_URL = "https://auth.globus.org/v2/oauth2/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://auth.globus.org/v2/oauth2/token"
    _OAUTH_USERINFO_URL = "https://auth.globus.org/v2/oauth2/userinfo"
    _OAUTH_SETTINGS_KEY = "globus_oauth"

    @_auth_return_future
    def get_tokens(self, key, secret, redirect_uri, code, callback):
        http = self.get_auth_http_client()
        body = urllib_parse.urlencode({
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": key,
            "client_secret": secret,
            "grant_type": "authorization_code"
        })
        fut = http.fetch(
            self._OAUTH_ACCESS_TOKEN_URL,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=body)
        fut.add_done_callback(wrap(functools.partial(self._on_access_token,
                                                     callback)))

    def _on_access_token(self, future, response_fut):
        """Callback function for the exchange to the access token."""
        try:
            response = response_fut.result()
        except Exception as e:
            future.set_exception(AuthError('Globus auth error: %s' % str(e)))
            return

        args = escape.json_decode(response.body)
        future_set_result_unless_cancelled(future, args)

    def get_user_info(self, access_token):
        return self.oauth2_request(self._OAUTH_USERINFO_URL,
                                   access_token=access_token)

    @_auth_return_future
    def oauth2_request(self, url, callback, access_token=None,
                       post_args=None, *args):
        headers = {}
        if access_token:
            headers = {"Authorization": "Bearer " + access_token}
        if args:
            url += "?" + urllib_parse.urlencode(args)
        callback = wrap(functools.partial(self._on_oauth2_request, callback))
        http = self.get_auth_http_client()
        if post_args is not None:
            fut = http.fetch(url, method="POST", headers=headers,
                             body=urllib_parse.urlencode(post_args))
        else:
            fut = http.fetch(url, headers=headers)
        fut.add_done_callback(callback)
