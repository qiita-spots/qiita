# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from collections import defaultdict

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction
from qiita_db.artifact import Artifact
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import check_access


html_error_message = "<b>An error occurred %s %s</b></br>%s"


def _to_int(value):
    """Transforms `value` to an integer

    Parameters
    ----------
    value : str or int
        The value to transform

    Returns
    -------
    int
        `value` as an integer

    Raises
    ------
    HTTPError
        If `value` cannot be transformed to an integer
    """
    try:
        res = int(value)
    except ValueError:
        raise HTTPError(500, "%s cannot be converted to an integer" % value)
    return res


class PreprocessingSummaryHandler(BaseHandler):
    @execute_as_transaction
    def _get_template_variables(self, preprocessed_data_id, callback):
        """Generates all the variables needed to render the template

        Parameters
        ----------
        preprocessed_data_id : int
            The preprocessed data identifier
        callback : function
            The callback function to call with the results once the processing
            is done

        Raises
        ------
        HTTPError
            If the preprocessed data does not have a log file
        """
        # Get the objects and check user privileges
        ppd = Artifact(preprocessed_data_id)
        study = ppd.study
        check_access(self.current_user, study, raise_error=True)

        # Get the return address
        back_button_path = self.get_argument(
            'back_button_path',
            '/study/description/%d?top_tab=preprocessed_data_tab&sub_tab=%s'
            % (study.id, preprocessed_data_id))

        # Get all the filepaths attached to the preprocessed data
        files_tuples = ppd.filepaths

        # Group the files by filepath type
        files = defaultdict(list)
        for _, fp, fpt in files_tuples:
            files[fpt].append(fp)

        try:
            log_path = files['log'][0]
        except KeyError:
            raise HTTPError(500, "Log file not found in preprocessed data %s"
                                 % preprocessed_data_id)

        with open(log_path, 'U') as f:
            contents = f.read()
            contents = contents.replace('\n', '<br/>')
            contents = contents.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

        title = 'Preprocessed Data: %d' % preprocessed_data_id

        callback((title, contents, back_button_path))

    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, preprocessed_data_id):
        ppd_id = _to_int(preprocessed_data_id)

        title, contents, back_button_path = yield Task(
            self._get_template_variables, ppd_id)

        self.render('text_file.html', title=title, contents=contents,
                    back_button_path=back_button_path)
