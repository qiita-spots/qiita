# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

from random import choice

from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_db.study import Study
from .base_handlers import BaseHandler


class StatsHandler(BaseHandler):
    @execute_as_transaction
    def _get_stats(self, callback):
        stats = {}
        # checking values from redis
        portal = qiita_config.portal
        vals = [
            ('number_studies', r_client.hgetall),
            ('number_of_samples', r_client.hgetall),
            ('num_users', r_client.get),
            ('lat_longs', r_client.get),
            ('num_studies_ebi', r_client.get),
            ('num_samples_ebi', r_client.get),
            ('number_samples_ebi_prep', r_client.get),
            ('img', r_client.get),
            ('time', r_client.get)]
        for k, f in vals:
            redis_key = '%s:stats:%s' % (portal, k)
            stats[k] = f(redis_key)

        callback(stats)

    @coroutine
    @execute_as_transaction
    def get(self):
        stats = yield Task(self._get_stats)

        # Pull a random public study from the database
        public_studies = Study.get_by_status('public')
        study = choice(list(public_studies)) if public_studies else None

        if study is None:
            random_study_info = None
            random_study_title = None
            random_study_id = None
        else:
            random_study_info = study.info
            random_study_title = study.title
            random_study_id = study.id

        self.render('stats.html',
                    number_studies=stats['number_studies'],
                    number_of_samples=stats['number_of_samples'],
                    num_users=stats['num_users'],
                    lat_longs=eval(
                        stats['lat_longs']) if stats['lat_longs'] else [],
                    num_studies_ebi=stats['num_studies_ebi'],
                    num_samples_ebi=stats['num_samples_ebi'],
                    number_samples_ebi_prep=stats['number_samples_ebi_prep'],
                    img=stats['img'], time=stats['time'],
                    random_study_info=random_study_info,
                    random_study_title=random_study_title,
                    random_study_id=random_study_id)
