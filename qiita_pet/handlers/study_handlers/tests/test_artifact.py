# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from os.path import exists, join
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.artifact import Artifact
from qiita_db.util import get_count, get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate


class ArtifactGraphAJAXTests(TestHandlerBase):
    def test_get_ancestors(self):
        response = self.get('/artifact/graph/', {'direction': 'ancestors',
                                                 'artifact_id': 1})
        exp = {'status': 'success',
               'message': '',
               'node_labels': [[1, 'Raw data 1 - FASTQ']],
               'edge_list': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_get_descendants(self):
        response = self.get('/artifact/graph/', {'direction': 'descendants',
                                                 'artifact_id': 1})
        exp = {'status': 'success',
               'message': '',
               'node_labels': [[1, 'Raw data 1 - FASTQ'],
                               [3, 'Demultiplexed 2 - Demultiplexed'],
                               [2, 'Demultiplexed 1 - Demultiplexed'],
                               [4, 'BIOM - BIOM'],
                               [5, 'BIOM - BIOM']],
               'edge_list': [[1, 3], [1, 2], [2, 4], [2, 5]]}
        self.assertEqual(response.code, 200)
        self.assertItemsEqual(loads(response.body), exp)

    def test_get_unknown(self):
        response = self.get('/artifact/graph/', {'direction': 'BAD',
                                                 'artifact_id': 1})
        exp = {'status': 'error',
               'message': 'Unknown directon BAD'}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)


class NewArtifactHandlerTests(TestHandlerBase):
    database = True

    def tearDown(self):
        # Replace file if removed as part of function testing
        uploads_path = get_mountpoint('uploads')[0][1]
        fp = join(uploads_path, '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

    def test_get(self):
        response = self.get('/study/add_prep/1')
        self.assertEqual(response.code, 200)
        self.assertIn('Select file type', response.body)
        self.assertIn('uploaded_file.txt', response.body)

    def test_get_files_not_allowed(self):
        response = self.post(
            '/study/prep_files/',
            {'type': 'BIOM', 'prep_file': 'uploaded_file.txt', 'study_id': 1})
        self.assertEqual(response.code, 405)

    def test_post_artifact(self):
        new_artifact_id = get_count('qiita.artifact') + 1
        new_prep_id = get_count('qiita.prep_template') + 1
        uploads_path = get_mountpoint('uploads')[0][1]
        # Create prep test file to point at
        prep_fp = join(uploads_path, '1', 'prep_create.txt')
        with open(prep_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")
        prep_fp = join(uploads_path, '1', 'uploaded_file.txt')
        with open(prep_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

        response = self.post(
            '/study/add_prep/1', {
                'name': 'new prep', 'data-type': '16S',
                'ena-ontology': 'Metagenomics', 'user-ontology': '',
                'new-ontology': '', 'type': 'per_sample_FASTQ',
                'prep-file': 'prep_create.txt',
                'raw_forward_seqs': ['uploaded_file.txt'],
                'raw_reverse_seqs': []})
        self.assertEqual(response.code, 200)
        # make sure new artifact created
        artifact = Artifact(new_artifact_id)
        self.assertEqual(artifact.name, 'new prep')
        PrepTemplate(new_prep_id)


class ArtifactAJAXTests(TestHandlerBase):
    database = True

    def test_delete_artifact(self):
        response = self.post('/artifact/',
                             {'artifact_id': 2})
        self.assertEqual(response.code, 200)

        # checking that the action was sent
        self.assertIn("Cannot delete artifact 2: it has children: 4",
                      response.body)


class ArtifactAdminAJAXTests(TestHandlerBase):
    databse = True

    def test_get_admin(self):
        response = self.get('/admin/artifact/',
                            {'artifact_id': 3})
        self.assertEqual(response.code, 200)

        # checking that proper actions shown
        self.assertIn("Make public</button>", response.body)
        self.assertIn("Revert to sandbox</button>", response.body)
        self.assertIn("Submit to EBI</a>", response.body)
        self.assertIn("Submit to VAMPS</a>", response.body)

    def test_post_admin(self):
        response = self.post('/admin/artifact/',
                             {'artifact_id': 3,
                              'visibility': 'sandbox'})
        self.assertEqual(response.code, 200)

        # checking that proper actions shown
        self.assertEqual({"status": "success",
                          "message": "Artifact visibility changed to sandbox"},
                         loads(response.body))

        self.assertEqual(Artifact(3).visibility, 'sandbox')

if __name__ == "__main__":
    main()
