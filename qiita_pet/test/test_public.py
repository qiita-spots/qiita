# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_db.artifact import Artifact
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestPublicHandler(TestHandlerBase):
    def test_public(self):
        response = self.get("/public/")
        self.assertEqual(response.code, 422)
        self.assertIn(
            "You need to specify study_id or artifact_id", response.body.decode("ascii")
        )

        response = self.get("/public/?study_id=100")
        self.assertEqual(response.code, 422)
        self.assertIn("Study 100 doesn&#39;t exist", response.body.decode("ascii"))

        response = self.get("/public/?artifact_id=100")
        self.assertEqual(response.code, 422)
        self.assertIn("Artifact 100 doesn&#39;t exist", response.body.decode("ascii"))

        response = self.get("/public/?artifact_id=1")
        self.assertEqual(response.code, 422)
        self.assertIn("Artifact 1 is not public", response.body.decode("ascii"))

        response = self.get("/public/?study_id=1")
        self.assertEqual(response.code, 422)
        self.assertIn("Not a public study", response.body.decode("ascii"))

        # artifact 1 is the first artifact within Study 1
        Artifact(1).visibility = "public"

        response = self.get("/public/?study_id=1")
        self.assertEqual(response.code, 200)

        response = self.get("/public/?artifact_id=1")
        self.assertEqual(response.code, 200)

        response = self.get("/public/?artifact_id=7")
        self.assertEqual(response.code, 422)
        self.assertIn("Artifact 7 is not public", response.body.decode("ascii"))

        # artifact 8 is part of an analysis
        Artifact(8).visibility = "public"

        response = self.get("/public/?artifact_id=8")
        self.assertEqual(response.code, 422)
        self.assertIn(
            "Artifact 8 doesn&#39;t belong to a study", response.body.decode("ascii")
        )


if __name__ == "__main__":
    main()
