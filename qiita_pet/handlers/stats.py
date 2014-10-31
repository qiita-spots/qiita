from __future__ import division

from datetime import datetime
from random import choice

from tornado.web import authenticated, HTTPError, asynchronous
from tornado.gen import coroutine, Task

from qiita_ware import r_server
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.util import get_count
from qiita_db.study import Study
from .base_handlers import BaseHandler

class StatsHandler(BaseHandler):
    def _get_stats(self, callback):
        # check if the key exists in redis
        lats = r_server.lrange('stats:sample_lats', 0, -1)
        longs = r_server.lrange('stats:sample_longs', 0, -1)
        times = r_server.lrange('stats:sample_times', 0, -1)
        if not (lats or longs or times):
            # if we don't have them, then fetch from disk and add to the
            # redis server with a 1-hour expiration
            conn = SQLConnectionHandler()
            sql = """select latitude, longitude, collection_timestamp
                     from qiita.required_sample_info"""
            lat_long_times = conn.execute_fetchall(sql)
            with r_server.pipeline() as pipe:
                for latitude, longitude, time in lat_long_times:
                    # storing as a simple data structure, hopefully this doesn't
                    # burn us later
                    pipe.rpush('stats:sample_lats', latitude)
                    pipe.rpush('stats:sample_longs', longitude)
                    pipe.rpush('stats:sample_times', time)

                # set the key to expire in an hour, so that we limit the number of
                # times we have to go to the database to a reasonable amount
                r_server.expire('stats:sample_lats', 3600)
                r_server.expire('stats:sample_longs', 3600)
                r_server.expire('stats:sample_times', 3600)

                pipe.execute()
        else:
            # If we do have them, put the redis results into the same structure
            # that would come back from the database
            times = [datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for t in times]
            longs = [float(x) for x in longs]
            lats = [float(x) for x in lats]
            lat_long_times = zip(lats, longs, times)

        # Get the number of studies
        num_studies = get_count('qiita.study')

        # Get the number of samples
        num_samples = len(lats)

        # Get the number of users
        num_users = get_count('qiita.qiita_user')

        callback([num_studies, num_samples, num_users, lat_long_times])

    @coroutine
    def get(self):
        num_studies, num_samples, num_users, lat_long_times = \
            yield Task(self._get_stats)

        # Pull a random public study from the database
        study = Study(choice(Study.get_public()))

        self.render('stats.html', user=self.current_user,
                    num_studies=num_studies, num_samples=num_samples,
                    num_users=num_users, lat_long_times=lat_long_times,
                    random_study_info=study.info,
                    random_study_title=study.title, random_study_id=study.id)
