# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import dumps
from future.utils import viewitems
from collections import defaultdict

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task
from pyparsing import ParseException
from moi import r_client

from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.search import QiitaStudySearch
from qiita_db.logger import LogEntry
from qiita_db.exceptions import QiitaDBIncompatibleDatatypeError
from qiita_db.util import (add_message, generate_study_list)
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import (
    study_person_linkifier, doi_linkifier, pubmed_linkifier, check_access,
    get_shared_links)


@execute_as_transaction
def _build_study_info(user, study_proc=None, proc_samples=None):
    """Builds list of dicts for studies table, with all HTML formatted

    Parameters
    ----------
    user : User object
        logged in user
    study_proc : dict of lists, optional
        Dictionary keyed on study_id that lists all processed data associated
        with that study. Required if proc_samples given.
    proc_samples : dict of lists, optional
        Dictionary keyed on proc_data_id that lists all samples associated with
        that processed data. Required if study_proc given.

    Returns
    -------
    infolist: list of dict of lists and dicts
        study and processed data info for JSON serialiation for datatables
        Each dict in the list is a single study, and contains the text

    Notes
    -----
    Both study_proc and proc_samples must be passed, or neither passed.
    """
    build_samples = False
    # Logic check to make sure both needed parts passed
    if study_proc is not None and proc_samples is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass proc_samples when study_proc given')
    elif proc_samples is not None and study_proc is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass study_proc when proc_samples given')
    elif study_proc is None:
        build_samples = True

    # get list of studies for table
    study_set = user.user_studies.union(
        Study.get_by_status('public')).union(user.shared_studies)
    if study_proc is not None:
        study_set = study_set.intersection(study_proc)
    if not study_set:
        # No studies left so no need to continue
        return []

    return generate_study_list([s.id for s in study_set], build_samples)


class ListStudiesHandler(BaseHandler):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, message="", msg_level=None):
        self.render('list_studies.html', message=message, msg_level=msg_level)

    def _get_all_emails(self, callback):
        callback(list(User.iter()))


class StudyApprovalList(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        user = self.current_user
        if user.level != 'admin':
            raise HTTPError(403, 'User %s is not admin' % self.current_user)

        studies = defaultdict(list)
        for artifact in Artifact.iter_by_visibility('awaiting_approval'):
            studies[artifact.study].append(artifact.id)
        parsed_studies = [(s.id, s.title, s.owner.email, pds)
                          for s, pds in viewitems(studies)]

        self.render('admin_approval.html',
                    study_info=parsed_studies)


class AutocompleteHandler(BaseHandler):
    @authenticated
    def get(self):
        text = self.get_argument('text')
        vals = r_client.execute_command('zrangebylex', 'qiita-usernames',
                                        u'[%s' % text, u'[%s\xff' % text)
        self.write({'results': [{'id': s, 'text': s} for s in vals]})


class ShareStudyAJAX(BaseHandler):
    @execute_as_transaction
    def _get_shared_for_study(self, study, callback):
        shared_links = get_shared_links(study)
        users = [u.email for u in study.shared_with]
        callback((users, shared_links))

    @execute_as_transaction
    def _share(self, study, user, callback):
        user = User(user)
        add_message('Study <a href="%s/study/description/%d">\'%s\'</a> '
                    'has been shared with you.' %
                    (qiita_config.portal_dir, study.id, study.title), [user])
        callback(study.share(user))

    @execute_as_transaction
    def _unshare(self, study, user, callback):
        user = User(user)
        add_message('Study \'%s\' has been unshared from you.' %
                    study.title, [user])
        callback(study.unshare(user))

    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self):
        study_id = int(self.get_argument('id'))
        study = Study(study_id)
        check_access(self.current_user, study, no_public=True,
                     raise_error=True)

        selected = self.get_argument('selected', None)
        deselected = self.get_argument('deselected', None)

        if selected is not None:
            yield Task(self._share, study, selected)
        if deselected is not None:
            yield Task(self._unshare, study, deselected)

        users, links = yield Task(self._get_shared_for_study, study)

        self.write(dumps({'users': users, 'links': links}))


class SearchStudiesAJAX(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, ignore):
        user = self.get_argument('user')
        query = self.get_argument('query')
        echo = int(self.get_argument('sEcho'))

        if user != self.current_user.id:
            raise HTTPError(403, 'Unauthorized search!')
        if query:
            # Search for samples matching the query
            search = QiitaStudySearch()
            try:
                search(query, self.current_user)
                study_proc, proc_samples, _ = search.filter_by_processed_data()
            except ParseException:
                self.clear()
                self.set_status(400)
                self.write('Malformed search query. Please read "search help" '
                           'and try again.')
                return
            except QiitaDBIncompatibleDatatypeError as e:
                self.clear()
                self.set_status(400)
                searchmsg = ''.join(e)
                self.write(searchmsg)
                return
            except Exception as e:
                # catch any other error as generic server error
                self.clear()
                self.set_status(500)
                self.write("Server error during search. Please try again "
                           "later")
                LogEntry.create('Runtime', str(e),
                                info={'User': self.current_user.id,
                                      'query': query})
                return
        else:
            study_proc = proc_samples = None
        info = _build_study_info(self.current_user, study_proc=study_proc,
                                 proc_samples=proc_samples)
        # linkifying data
        len_info = len(info)
        for i in range(len_info):
            info[i]['shared'] = ", ".join([study_person_linkifier(element)
                                           for element in info[i]['shared']])
            info[i]['pmid'] = ", ".join([pubmed_linkifier([element])
                                         for element in info[i]['pmid']])
            info[i]['publication_doi'] = ", ".join([
                doi_linkifier([element])
                for element in info[i]['publication_doi']])
            info[i]['pi'] = study_person_linkifier(info[i]['pi'])
            info[i]['ebi_info'] = '%s (%s)' % (
                ''.join([
                    '<a href="https://www.ebi.ac.uk/ena/data/view/{0}">{0}'
                    '</a></br>'.format(acc)
                    for acc in info[i]['ebi_study_accession'].split(',')]),
                info[i]['ebi_submission_status'])

        # build the table json
        results = {
            "sEcho": echo,
            "iTotalRecords": len_info,
            "iTotalDisplayRecords": len_info,
            "aaData": info
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))
