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

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task
from pyparsing import ParseException

from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.search import QiitaStudySearch
from qiita_db.metadata_template import SampleTemplate
from qiita_db.logger import LogEntry
from qiita_db.exceptions import QiitaDBIncompatibleDatatypeError
from qiita_db.util import get_table_cols
from qiita_db.data import ProcessedData
from qiita_core.exceptions import IncompetentQiitaDeveloperError

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import study_person_linkifier, pubmed_linkifier


def _get_shared_links_for_study(study):
    shared = []
    for person in study.shared_with:
        person = User(person)
        name = person.info['name']
        email = person.email
        # Name is optional, so default to email if non existant
        if name:
            shared.append(study_person_linkifier(
                (email, name)))
        else:
            shared.append(study_person_linkifier(
                (email, email)))
    return ", ".join(shared)


def _build_study_info(user, study_proc=None, proc_samples=None):
    """builds list of dicts for studies table, with all html formatted

    Parameters
    ----------
    user : User object
        logged in user
    study_proc : dict of lists
        Dictionary keyed on study_id that lists all processed data associated
        with that study.
    proc_samples : dict of lists
        Dictionary keyed on proc_data_id that lists all samples associated with
        that processed data.

    Notes
    -----
    Both study_proc and proc_samples must be passed, or neither passed.
    """
    # Logic check to make sure both needed parts passed
    if study_proc is not None and proc_samples is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass proc_samples when study_proc given')
    elif proc_samples is not None and study_proc is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass study_proc when proc_samples given')

    # get list of studies for table
    study_list = user.user_studies.union(
        Study.get_by_status('public')).union(user.shared_studies)
    if study_proc is not None:
        study_list = study_list.intersection(study_proc)
    if not study_list:
        # No studies left so no need to continue
        return []

    # get info for the studies
    cols = ['study_id', 'email', 'principal_investigator_id',
            'pmid', 'study_title', 'metadata_complete',
            'number_samples_collected', 'study_abstract']
    study_info = Study.get_info(study_list, cols)

    infolist = []
    for row, info in enumerate(study_info):
        study = Study(info['study_id'])
        status = study.status
        # if needed, get all the proc data info since no search results passed
        if study_proc is None:
            proc_data = study.processed_data()
            proc_samples = {}
            study_proc = {study.id: proc_data}
            for pid in proc_data:
                proc_samples[pid] = ProcessedData(pid).samples
        # Just passing the email address as the name here, since
        # name is not a required field in qiita.qiita_user
        PI = StudyPerson(info['principal_investigator_id'])
        PI = study_person_linkifier((PI.email, PI.name))
        if info['pmid'] is not None:
            pmids = ", ".join([pubmed_linkifier([p])
                               for p in info['pmid']])
        else:
            pmids = ""
        if info["number_samples_collected"] is None:
            info["number_samples_collected"] = "0"
        shared = _get_shared_links_for_study(study)
        meta_complete_glyph = "ok" if info["metadata_complete"] else "remove"
        # build the HTML elements needed for table cell
        title = ("<a href='#' data-toggle='modal' "
                 "data-target='#study-abstract-modal' "
                 "onclick='fillAbstract(\"studies-table\", {0})'>"
                 "<span class='glyphicon glyphicon-file' "
                 "aria-hidden='true'></span></a> | "
                 "<a href='/study/description/{1}' "
                 "id='study{0}-title'>{2}</a>").format(
                     str(row), str(study.id), info["study_title"])
        meta_complete = "<span class='glyphicon glyphicon-%s'></span>" % \
            meta_complete_glyph
        if status == 'public':
            shared = "Not Available"
        else:
            shared = ("<span id='shared_html_{0}'>{1}</span><br/>"
                      "<a class='btn btn-primary btn-xs' data-toggle='modal' "
                      "data-target='#share-study-modal-view' "
                      "onclick='modify_sharing({0});'>Modify</a>".format(
                          study.id, shared))
        # Build the proc data info list for the child row in datatable
        proc_data_info = []
        for pid in study_proc[study.id]:
            proc_data = ProcessedData(pid)
            info = proc_data.processing_info
            info['pid'] = pid
            info['samples'] = proc_samples[pid]
            proc_data_info.append(info)

        infolist.append({
            "checkbox": "<input type='checkbox' value='%d' />" % study.id,
            "id": study.id,
            "title": title,
            "meta_complete": meta_complete,
            "num_samples": info["number_samples_collected"],
            "shared": shared,
            "num_raw_data": len(study.raw_data()),
            "pi": PI,
            "pmid": pmids,
            "status": status,
            "abstract": info["study_abstract"],
            "proc_data_info": proc_data_info
        })
    return infolist


def _check_owner(user, study):
    """make sure user is the owner of the study requested"""
    if not user.id == study.owner:
        raise HTTPError(403, "User %s does not own study %d" %
                        (user.id, study.id))


class ListStudiesHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        all_emails_except_current = yield Task(self._get_all_emails)
        all_emails_except_current.remove(self.current_user.id)
        avail_meta = SampleTemplate.metadata_headers() +\
            get_table_cols("study")
        self.render('list_studies.html', availmeta=avail_meta,
                    all_emails_except_current=all_emails_except_current)

    def _get_all_emails(self, callback):
        callback(list(User.iter()))


class StudyApprovalList(BaseHandler):
    @authenticated
    def get(self):
        user = self.current_user
        if user.level != 'admin':
            raise HTTPError(403, 'User %s is not admin' % self.current_user)

        result_generator = viewitems(
            ProcessedData.get_by_status_grouped_by_study('awaiting_approval'))
        study_generator = ((Study(sid), pds) for sid, pds in result_generator)
        parsed_studies = [(s.id, s.title, s.owner, pds)
                          for s, pds in study_generator]

        self.render('admin_approval.html',
                    study_info=parsed_studies)


class ShareStudyAJAX(BaseHandler):
    def _get_shared_for_study(self, study, callback):
        shared_links = _get_shared_links_for_study(study)
        users = study.shared_with
        callback((users, shared_links))

    def _share(self, study, user, callback):
        user = User(user)
        callback(study.share(user))

    def _unshare(self, study, user, callback):
        user = User(user)
        callback(study.unshare(user))

    @authenticated
    @coroutine
    def get(self):
        study_id = int(self.get_argument('study_id'))
        study = Study(study_id)
        _check_owner(self.current_user, study)

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
    def get(self, ignore):
        user = self.get_argument('user')
        query = self.get_argument('query')
        echo = int(self.get_argument('sEcho'))

        if user != self.current_user.id:
            raise HTTPError(403, 'Unauthorized search!')
        res = None
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
        # build the table json
        results = {
            "sEcho": echo,
            "iTotalRecords": len(info),
            "iTotalDisplayRecords": len(info),
            "aaData": info
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))
