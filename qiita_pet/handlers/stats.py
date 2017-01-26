from __future__ import division

from random import choice

from moi import r_client
from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_db.study import Study
from .base_handlers import BaseHandler


class StatsHandler(BaseHandler):
    @execute_as_transaction
    def _get_stats(self, callback):
        # initializing values
        number_studies, number_of_samples, num_users, time = '', '', '', ''
        lat_longs, num_studies_ebi, num_samples_ebi, img = '', '', '', ''
        number_samples_ebi_prep = ''

        # checking values from redis
        portal = qiita_config.portal
        keys = [
            'number_studies', 'number_of_samples', 'num_users', 'lat_longs',
            'num_studies_ebi', 'num_samples_ebi', 'number_samples_ebi_prep',
            'img', 'time']

        for k in keys:
            redis_key = '%s:stats:%s' % (portal, k)
            # retrieving dicts
            if k == 'number_studies':
                number_studies = r_client.hgetall(redis_key)
            elif k == 'number_of_samples':
                number_of_samples = r_client.hgetall(redis_key)
            # single values
            elif k == 'num_users':
                num_users = r_client.get(redis_key)
            elif k == 'num_studies_ebi':
                num_studies_ebi = r_client.get(redis_key)
            elif k == 'num_samples_ebi':
                num_samples_ebi = r_client.get(redis_key)
            elif k == 'num_samples_ebi':
                num_samples_ebi = r_client.get(redis_key)
            elif k == 'number_samples_ebi_prep':
                number_samples_ebi_prep = r_client.get(redis_key)
            elif k == 'img':
                img = r_client.get(redis_key)
            elif k == 'time':
                time = r_client.get(redis_key)
            # storing tuples and single values
            elif k == 'lat_longs':
                lat_longs = eval(r_client.get(redis_key))

        callback([number_studies, number_of_samples, num_users, lat_longs,
                  num_studies_ebi, num_samples_ebi, number_samples_ebi_prep,
                  img, time])

    @coroutine
    @execute_as_transaction
    def get(self):
        number_studies, number_of_samples, num_users, lat_longs, \
            num_studies_ebi, num_samples_ebi, number_samples_ebi_prep, \
            img, time = yield Task(self._get_stats)

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
                    number_studies=number_studies,
                    number_of_samples=number_of_samples, num_users=num_users,
                    lat_longs=lat_longs, num_studies_ebi=num_studies_ebi,
                    num_samples_ebi=num_samples_ebi,
                    number_samples_ebi_prep=number_samples_ebi_prep,
                    img=img, time=time,
                    random_study_info=random_study_info,
                    random_study_title=random_study_title,
                    random_study_id=random_study_id)
