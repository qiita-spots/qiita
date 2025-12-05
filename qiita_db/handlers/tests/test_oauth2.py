# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from json import loads
from unittest import main

from qiita_core.qiita_settings import r_client
from qiita_pet.test.tornado_test_base import TestHandlerBase


class OAuth2BaseHandlerTests(TestHandlerBase):
    def setUp(self):
        # Create client test authentication token
        self.client_token = "SOMEAUTHTESTINGTOKENHERE2122"
        token_info = {
            "timestamp": "12/12/12 12:12:00",
            "client_id": "test123123123",
            "grant_type": "client",
        }
        r_client.hmset(self.client_token, token_info)
        r_client.expire(self.client_token, 5)

        # Create username test authentication token
        self.user_token = "SOMEAUTHTESTINGTOKENHEREUSERNAME"
        token_info = {
            "timestamp": "12/12/12 12:12:00",
            "client_id": "testuser",
            "grant_type": "password",
            "user": "test@foo.bar",
        }
        r_client.hmset(self.user_token, token_info)
        r_client.expire(self.user_token, 5)

        # Create test access limit token
        self.user_rate_key = "testuser_test@foo.bar_daily_limit"
        r_client.setex(self.user_rate_key, 5, 2)
        super(OAuth2BaseHandlerTests, self).setUp()

    def test_authenticate_header_client(self):
        obs = self.get(
            "/qiita_db/artifacts/1/",
            headers={"Authorization": "Bearer " + self.client_token},
        )
        self.assertEqual(obs.code, 200)

    def test_authenticate_header_username(self):
        obs = self.get(
            "/qiita_db/artifacts/1/",
            headers={"Authorization": "Bearer " + self.user_token},
        )
        self.assertEqual(obs.code, 200)

        # Check rate limiting works
        self.assertEqual(int(r_client.get(self.user_rate_key)), 1)
        r_client.setex("testuser_test@foo.bar_daily_limit", 1, 0)
        obs = self.get(
            "/qiita_db/artifacts/100/",
            headers={"Authorization": "Bearer " + self.user_token},
        )
        exp = {
            "error": "invalid_grant",
            "error_description": "Oauth2 error: daily request limit reached",
        }
        self.assertEqual(loads(obs.body), exp)

    def test_authenticate_header_missing(self):
        obs = self.get("/qiita_db/artifacts/100/")
        self.assertEqual(obs.code, 400)
        self.assertEqual(
            loads(obs.body),
            {
                "error": "invalid_request",
                "error_description": "Oauth2 error: invalid access token",
            },
        )

    def test_authenticate_header_bad_token(self):
        obs = self.get(
            "/qiita_db/artifacts/100/", headers={"Authorization": "Bearer BADTOKEN"}
        )
        self.assertEqual(obs.code, 400)
        exp = {
            "error": "invalid_grant",
            "error_description": "Oauth2 error: token has timed out",
        }
        self.assertEqual(loads(obs.body), exp)

    def test_authenticate_header_bad_header_type(self):
        obs = self.get(
            "/qiita_db/artifacts/100/",
            headers={"Authorization": "WRONG " + self.client_token},
        )
        self.assertEqual(obs.code, 400)
        exp = {
            "error": "invalid_grant",
            "error_description": "Oauth2 error: invalid access token",
        }
        self.assertEqual(loads(obs.body), exp)


class OAuth2HandlerTests(TestHandlerBase):
    def test_authenticate_client_header(self):
        # Authenticate using header
        obs = self.post(
            "/qiita_db/authenticate/",
            {"grant_type": "client"},
            {
                "Authorization": "Basic MTluZGtPM29NS3NvQ2hqVlZXbHVGN1FreEhSZl"
                "loVEtTRmJBVnQ4SWhLN2daZ0RhTzQ6SjdGZlE3Q1FkT3"
                "h1S2hRQWYxZW9HZ0JBRTgxTnM4R3UzRUthV0ZtM0lPMk"
                "pLaEFtbUNXWnVhYmUwTzVNcDI4czE="
            },
        )
        self.assertEqual(obs.code, 200)
        obs_body = loads(obs.body)
        exp = {
            "access_token": obs_body["access_token"],
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        self.assertDictEqual(obs_body, exp)

        # Make sure token in system with proper ttl
        token = r_client.hgetall(obs_body["access_token"])
        exp = {
            b"timestamp": token[b"timestamp"],
            b"client_id": (b"19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4"),
            b"grant_type": b"client",
        }
        self.assertDictEqual(token, exp)
        self.assertEqual(r_client.ttl(obs_body["access_token"]), 3600)

    def test_authenticate_client_post(self):
        # Authenticate using post only
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "client",
                "client_id": "19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4",
                "client_secret": "J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2J"
                "KhAmmCWZuabe0O5Mp28s1",
            },
        )
        self.assertEqual(obs.code, 200)
        obs_body = loads(obs.body)
        exp = {
            "access_token": obs_body["access_token"],
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        self.assertDictEqual(obs_body, exp)

        # Make sure token in system with proper ttl
        token = r_client.hgetall(obs_body["access_token"])
        exp = {
            b"timestamp": token[b"timestamp"],
            b"client_id": (b"19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4"),
            b"grant_type": b"client",
        }
        self.assertDictEqual(token, exp)
        self.assertEqual(r_client.ttl(obs_body["access_token"]), 3600)

    def test_authenticate_client_bad_base64_hash(self):
        # Authenticate using bad header
        obs = self.post(
            "/qiita_db/authenticate/",
            {"grant_type": "client"},
            {
                "Authorization": "Basic MTluZGtPM29NS3NvQ2hqVlZXbHVGN1FreEhSZl"
                "loVEtTRmJBVnQ4SBADN2daZ0RhTzQ6SjdGZlE3Q1FkT3"
                "h1S2hRQWYxZW9HZ0JBRTgxTnM4R3UzRUthV0ZtM0lPMk"
                "pLaEFtbUNXWnVhYmUwTzVNcDI4czE="
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_client_bad_header_base64_hash(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {"grant_type": "client"},
            {
                "Authorization": "WRONG MTluZGtPM29NS3NvQ2hqVlZXbHVGN1FreEhSZl"
                "loVEtTRmJBVnQ4SWhLN2daZ0RhTzQ6SjdGZlE3Q1FkT3"
                "h1S2hRQWYxZW9HZ0JBRTgxTnM4R3UzRUthV0ZtM0lPMk"
                "pLaEFtbUNXWnVhYmUwTzVNcDI4czE="
            },
        )
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_request",
            "error_description": "Oauth2 error: invalid token type",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_client_bad_client_id(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "client",
                "client_id": "BADdkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4",
                "client_secret": "J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2J"
                "KhAmmCWZuabe0O5Mp28s1",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_client_bad_client_secret(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "client",
                "client_id": "19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4",
                "client_secret": "BADfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2J"
                "KhAmmCWZuabe0O5Mp28s1",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_client_missing_info(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "client",
                "client_id": "19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_request",
            "error_description": "Oauth2 error: missing client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_password(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE",
                "username": "test@foo.bar",
                "password": "password",
            },
        )
        self.assertEqual(obs.code, 200)
        obs_body = loads(obs.body)
        exp = {
            "access_token": obs_body["access_token"],
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        self.assertDictEqual(obs_body, exp)

        # Make sure token in system with proper ttl
        token = r_client.hgetall(obs_body["access_token"])
        exp = {
            b"timestamp": token[b"timestamp"],
            b"user": b"test@foo.bar",
            b"client_id": token[b"client_id"],
            b"grant_type": b"password",
        }
        self.assertDictEqual(token, exp)
        self.assertEqual(r_client.ttl(obs_body["access_token"]), 3600)

    def test_authenticate_password_non_user_client_id_header(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4",
                "username": "test@foo.bar",
                "password": "password",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_password_non_user_client_id(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "WAAAAAAAAAARG",
                "username": "test@foo.bar",
                "password": "password",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid client information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_password_bad_user_id(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE",
                "username": "BROKEN@FAKE.COM",
                "password": "password",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid user information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_password_bad_password(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE",
                "username": "test@foo.bar",
                "password": "NOTAReALPASSworD",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_client",
            "error_description": "Oauth2 error: invalid user information",
        }
        self.assertEqual(obs_body, exp)

    def test_authenticate_password_missing_info(self):
        obs = self.post(
            "/qiita_db/authenticate/",
            {
                "grant_type": "password",
                "client_id": "DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE",
                "username": "test@foo.bar",
            },
        )
        self.assertEqual(obs.code, 400)
        obs_body = loads(obs.body)
        exp = {
            "error": "invalid_request",
            "error_description": "Oauth2 error: missing user information",
        }
        self.assertEqual(obs_body, exp)


if __name__ == "__main__":
    main()
