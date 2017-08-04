# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import warnings
from json import dumps
from copy import deepcopy

from tornado.web import authenticated, HTTPError

from qiita_core.util import execute_as_transaction
from qiita_db.study import Study
from qiita_db.portal import Portal
from qiita_db.exceptions import QiitaDBError
from .base_handlers import BaseHandler


class PortalEditBase(BaseHandler):
    study_cols = ['study_id', 'study_title', 'study_alias']

    def check_admin(self):
        if self.current_user.level != "admin":
            raise HTTPError(403, "%s does not have access to portal editing!" %
                            self.current_user.id)

    @execute_as_transaction
    def get_info(self, portal="QIITA"):
        # Add the portals and, optionally, checkbox to the information
        studies = [s.id for s in Portal(portal).get_studies()]
        if not studies:
            return []

        study_info = Study.get_info(studies, info_cols=self.study_cols)
        info = []
        for s in study_info:
            # Make sure in correct order
            hold = dict(s)
            hold['portals'] = ', '.join(sorted(Study(s['study_id'])._portals))
            info.append(hold)
        return info


class StudyPortalHandler(PortalEditBase):
    @authenticated
    @execute_as_transaction
    def get(self):
        self.check_admin()
        info = self.get_info()
        portals = Portal.list_portals()
        headers = deepcopy(self.study_cols)
        headers.insert(0, "portals")
        self.render('portals_edit.html', headers=headers, info=info,
                    portals=portals, submit_url="/admin/portals/studies/")

    @authenticated
    @execute_as_transaction
    def post(self):
        self.check_admin()
        portal = self.get_argument('portal')
        studies = map(int, self.get_arguments('selected'))
        action = self.get_argument('action')

        try:
            portal = Portal(portal)
        except:
            raise HTTPError(400, "Not valid portal: %s" % portal)
        try:
            with warnings.catch_warnings(record=True) as warns:
                if action == "Add":
                    portal.add_studies(studies)
                elif action == "Remove":
                    portal.remove_studies(studies)
                else:
                    raise HTTPError(400, "Unknown action: %s" % action)
        except QiitaDBError as e:
                self.write(action.upper() + " ERROR:<br/>" + str(e))
                return

        msg = '; '.join([str(w.message) for w in warns])
        self.write(action + " completed successfully<br/>" + msg)


class StudyPortalAJAXHandler(PortalEditBase):
    @authenticated
    @execute_as_transaction
    def get(self):
        self.check_admin()
        portal = self.get_argument('view-portal')
        echo = self.get_argument('sEcho')
        info = self.get_info(portal=portal)
        # build the table json
        results = {
            "sEcho": echo,
            "iTotalRecords": len(info),
            "iTotalDisplayRecords": len(info),
            "aaData": info
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))
