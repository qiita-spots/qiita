# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps

from tornado import gen
from tornado.web import HTTPError

import qiita_db as qdb

from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_analysis(a_id):
    """Returns the analysis with the given `a_id` if it exists

    Parameters
    ----------
    a_id : str
        The analysis id

    Returns
    -------
    qiita_db.analysis.Analysis
        The requested analysis

    Raises
    ------
    HTTPError
        If the analysis does not exist, with error code 404
        If there is a problem instantiating the analysis, with error code 500
    """
    try:
        a_id = int(a_id)
        a = qdb.analysis.Analysis(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(
            500, reason="Error instantiating analysis %s: %s" % (a_id, str(e))
        )
    return a


class APIAnalysisMetadataHandler(OauthBaseHandler):
    @authenticate_oauth
    async def get(self, analysis_id):
        """Retrieves the analysis metadata

        Parameters
        ----------
        analysis_id : str
            The id of the analysis whose information is being retrieved

        Returns
        -------
        dict
            The contents of the analysis keyed by sample id

        Notes
        -----
        This response needed to be broken in chunks because we were hitting
        the max size of a respose: 2G; based on: https://bit.ly/3CPvyjd
        """
        chunk_len = 1024 * 1024 * 1  # 1 MiB

        response = None
        with qdb.sql_connection.TRN:
            a = _get_analysis(analysis_id)
            mf_fp = qdb.util.get_filepath_information(a.mapping_file)["fullpath"]
            if mf_fp is not None:
                df = qdb.metadata_template.util.load_template_to_dataframe(
                    mf_fp, index="#SampleID"
                )
                response = dumps(df.to_dict(orient="index"))

        if response is not None:
            crange = range(chunk_len, len(response) + chunk_len, chunk_len)
            for i, (win) in enumerate(crange):
                # sending the chunk and flushing
                chunk = response[i * chunk_len : win]
                self.write(chunk)
                await self.flush()

                # cleaning chuck and pause the coroutine so other handlers
                # can run, note that this is required/important based on the
                # original implementation in https://bit.ly/3CPvyjd
                del chunk
                await gen.sleep(0.000000001)  # 1 nanosecond

        else:
            self.write(None)
