# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads
from os.path import basename

from tornado.web import HTTPError
import pandas as pd

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_prep_template(pid):
    """Returns the prep template with the given `pid` if it exists

    Parameters
    ----------
    pid : str
        The prep template id

    Returns
    -------
    qiita_db.metadata_template.prep_template.PrepTemplate
        The requested prep template

    Raises
    ------
    HTTPError
        If the prep template does not exist, with error code 404
        If there is a problem instantiating the template, with error code 500
    """
    try:
        pid = int(pid)
        pt = qdb.metadata_template.prep_template.PrepTemplate(pid)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason='Error instantiating prep template %s: %s'
                             % (pid, str(e)))

    return pt


class PrepTemplateDBHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, prep_id):
        """Retrieves the prep template information

        Parameters
        ----------
        prep_id: str
            The id of the prep template whose information is being retrieved

        Returns
        -------
        dict
            The prep information:
            'data_type': prep info data type
            'artifact': artifact attached to the given prep
            'investigation_type': prep info investigation type
            'study': study that the prep info belongs to
            'status': prep info status
            'qiime-map': the path to the qiime mapping file
            'prep-file': the path to the prep info file
        """
        with qdb.sql_connection.TRN:
            pt = _get_prep_template(prep_id)
            prep_files = [fp for _, fp in pt.get_filepaths()
                          if 'qiime' not in basename(fp)]
            artifact = pt.artifact.id if pt.artifact is not None else None
            response = {
                'data_type': pt.data_type(),
                'artifact': artifact,
                'investigation_type': pt.investigation_type,
                'study': pt.study_id,
                'status': pt.status,
                'qiime-map': pt.qiime_map_fp,
                # The first element in the prep_files is the newest
                # prep information file - hence the correct one
                'prep-file': prep_files[0]
            }

        self.write(response)


class PrepTemplateDataHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, prep_id):
        """Retrieves the prep contents

        Parameters
        ----------
        prep_id : str
            The id of the prep template whose information is being retrieved

        Returns
        -------
        dict
            The contents of the prep information keyed by sample id
        """
        with qdb.sql_connection.TRN:
            pt = _get_prep_template(prep_id)
            response = {'data': pt.to_dataframe().to_dict(orient='index')}

        self.write(response)


class PrepTemplateAPItestHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        prep_info_dict = loads(self.get_argument('prep_info'))
        study = self.get_argument('study')
        data_type = self.get_argument('data_type')

        metadata = pd.DataFrame.from_dict(prep_info_dict, orient='index')
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(study), data_type)
        self.write({'prep': pt.id})
