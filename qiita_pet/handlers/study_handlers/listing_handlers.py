# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from collections import namedtuple
from json import dumps

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.search import QiitaStudySearch
from qiita_db.metadata_template import SampleTemplate
from qiita_db.util import get_table_cols
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


def _build_study_info(studytype,  user, studies=None):
    """builds list of namedtuples for study listings"""
    if studytype not in {"standard", "shared"}:
        raise IncompetentQiitaDeveloperError("Must use private, shared, "
                                             "or public!")
    # get list of studies for table
    if studies is not None:
        # filter info to given studies
        if studytype == "standard":
            studylist = (user.user_studies |
                         Study.get_by_status('public')).intersection(studies)
        elif studytype == "shared":
            studylist = user.shared_studies.intersection(studies)
    elif studytype == "standard":
        studylist = user.user_studies | Study.get_by_status('public')
    elif studytype == "shared":
        studylist = user.shared_studies
    if not studylist:
        return set()
    StudyTuple = namedtuple('StudyInfo', 'id title meta_complete '
                            'num_samples_collected shared num_raw_data pi '
                            'pmids owner status abstract')
    cols = ['study_id', 'status', 'email', 'principal_investigator_id',
            'pmid', 'study_title', 'metadata_complete',
            'number_samples_collected', 'study_abstract']
    study_info = Study.get_info(studylist, cols)
    infolist = set()
    for info in study_info:
        study = Study(info['study_id'])
        # Just passing the email address as the name here, since
        # name is not a required field in qiita.qiita_user
        owner = study_person_linkifier((info['email'], info['email']))
        PI = StudyPerson(info['principal_investigator_id'])
        PI = study_person_linkifier((PI.email, PI.name))
        if info['pmid'] is not None:
            pmids = ", ".join([pubmed_linkifier([p])
                               for p in info['pmid']])
        else:
            pmids = ""
        shared = _get_shared_links_for_study(study)
        infolist.add(StudyTuple(
            study.id, study.title, info["metadata_complete"],
            info["number_samples_collected"], shared, len(study.raw_data()),
            PI, pmids, owner, info["status"], info["study_abstract"]))
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
        availmeta = SampleTemplate.metadata_headers() +\
            get_table_cols("study")
        self.render('list_studies.html', availmeta=availmeta,
                    all_emails_except_current=all_emails_except_current)

    def _get_all_emails(self, callback):
        callback(list(User.iter()))


class StudyApprovalList(BaseHandler):
    @authenticated
    def get(self):
        user = self.current_user
        if user.level != 'admin':
            raise HTTPError(403, 'User %s is not admin' % self.current_user)

        parsed_studies = []
        for sid in Study.get_by_status('awaiting_approval'):
            study = Study(sid)
            parsed_studies.append((study.id, study.title, study.owner))

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
    def _get_standard(self, user, callback):
        callback(_build_study_info("standard", user))

    def _get_shared(self, user, callback):
        """builds list of tuples for studies that are shared with user"""
        callback(_build_study_info("shared", user))

    @authenticated
    def get(self, ignore):
        search_type = self.get_argument('type')
        user = self.get_argument('user')
        query = self.get_argument('query')
        echo = int(self.get_argument('sEcho'))

        res = None
        if query != "":
            # Search for samples matching the query
            search = QiitaStudySearch()
            res, meta = search(query, User(user))
            info = _build_study_info(search_type, self.current_user,
                                     studies=res.keys())
        else:
            # show everything
            info = _build_study_info(search_type, self.current_user)
        # build the table json
        results = {
            "sEcho": echo,
            "iTotalRecords": len(info),
            "iTotalDisplayRecords": len(info),
            "aaData": []
        }
        if search_type == "standard":
            for row, s in enumerate(info):
                # build the HTML elements needed for table cell
                meta_complete = "ok" if s.meta_complete else "remove"
                share = "Not Available" if s.status == 'public' else \
                    ("<span id='shared_html_{0}'>{1}</span><br/>"
                     "<a class='btn btn-primary' data-toggle='modal' "
                     "data-target='#share-study-modal-view' "
                     "onclick='modify_sharing({0});'>Modify</a>".format(
                        s.id, s.shared))
                # add study to table
                results['aaData'].append([
                    "<input type='checkbox' value='%s'>" % s.id,

                    "<a href='#'' data-toggle='modal' "
                    "data-target='#study-abstract-modal' "
                    "onclick='fillAbstract(\"user-studies-table\", {0})'>"
                    "<span class=\'glyphicon glyphicon-file\' "
                    "aria-hidden=\'true\'></span></a> | "
                    "<a href=\'/study/description/{1}\' "
                    "id=\'study{0}-title\'>{2}</a>".format(
                        str(row), str(s.id), s.title),

                    s.abstract,
                    s.id,
                    "<span class='glyphicon glyphicon-%s'></span>" %
                    meta_complete,
                    s.num_samples_collected,
                    s.num_raw_data,
                    share,
                    s.pi,
                    s.pmids,
                    s.status
                ])
        elif search_type == "shared":
            for row, s in enumerate(info):
                # build the HTML elements needed for table cell
                meta_complete = "ok" if s.meta_complete else "remove"
                # add study to table
                results['aaData'].append([
                    "<input type='checkbox' value='%s'>" % s.id,

                    "<a href='#'' data-toggle='modal' "
                    "data-target='#study-abstract-modal' "
                    "onclick='fillAbstract(\"shared-studies-table\", {0})'>"
                    "<span class=\'glyphicon glyphicon-file\' "
                    "aria-hidden=\'true\'></span></a> | "
                    "<a href=\'/study/description/{1}\' "
                    "id=\'study{0}-title\'>{2}</a>".format(
                        str(row), str(s.id), s.title),

                    s.abstract,
                    s.id,
                    s.owner,
                    "<span class='glyphicon glyphicon-%s'></span>" %
                    meta_complete,
                    s.num_samples_collected,
                    s.num_raw_data,
                    s.pi,
                    s.pmids
                ])

        # return the json
        self.write(dumps(results))
