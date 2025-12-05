# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from time import sleep
from unittest import main

from requests import Request
from six import StringIO

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestStudyUploadFileHandler(TestHandlerBase):
    def test_get_exists(self):
        response = self.get("/study/upload/1")
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get("/study/upload/245")
        self.assertEqual(response.code, 404)


class TestUploadFileHandler(TestHandlerBase):
    def test_get(self):
        response = self.get("/upload/")
        self.assertEqual(response.code, 400)


class TestStudyUploadViaRemote(TestHandlerBase):
    def _setup_request(self, data):
        # setting up things to test by sending POST variables and a file
        # taken from: https://bit.ly/2CpZiZn
        prepare = Request(
            url="https://localhost/",
            files={"ssh-key": StringIO("Test key.")},
            data=data,
        ).prepare()
        headers = {"Content-Type": prepare.headers.get("Content-Type")}
        body = prepare.body

        return headers, body

    def test_post(self):
        data = {"remote-request-type": "list", "inputURL": "scp-url"}
        headers, body = self._setup_request(data)

        # study doesn't exist
        response = self.post("/study/upload/remote/100", data=body, headers=headers)
        self.assertEqual(response.code, 404)

        # create a successful list job
        response = self.post("/study/upload/remote/1", data=body, headers=headers)
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body.decode("ascii"), '{"status": "success", "message": ""}'
        )

        # create a successful list job
        data = {"remote-request-type": "transfer", "inputURL": "scp-url"}
        headers, body = self._setup_request(data)
        response = self.post("/study/upload/remote/1", data=body, headers=headers)
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body.decode("ascii"), '{"status": "success", "message": ""}'
        )
        # sleep to wait for jobs to finish, no need to check for it's status
        sleep(5)

        # jobs with bad Parameters
        data = {"remote-request-type": "error", "inputURL": "scp-url"}
        headers, body = self._setup_request(data)
        response = self.post("/study/upload/remote/1", data=body, headers=headers)
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body.decode("ascii"),
            '{"status": "error", "message": "Not a valid method"}',
        )


if __name__ == "__main__":
    main()
