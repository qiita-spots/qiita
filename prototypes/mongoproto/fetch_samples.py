#!/usr/bin/env python

import pymongo
import psycopg2
from biom.table import table_factory
from operator import itemgetter

def get_metadata(mongo_db, query):
    ids = []
    recs = []
    for rec in mongo_db.metadata.find(query):
        ids.append("%s::%s" % (rec['STUDY_ID'], rec['SampleID']))
        recs.append(rec)
    return ids, recs

def get_common(recs):
    keys = set([])
    for r in recs:
        keys.update(set(r.keys()))
    return keys

def fetch_table(pg_cur, ids, table):
    query = """select study_sample, observation, count
             from observations
             where table_id='%s' and study_sample in (%s)"""
    
    popped_query = query % (table, ','.join(["'%s'" % i for i in ids]))
    
    pg_cur.execute(popped_query)

    to_construct = [r for r in pg_cur.fetchall()]
    return to_construct
        
def fetch_all(pg_cur, ids):
    query = """select study_sample, observation, count
             from observations
             where study_sample in (%s)"""
    
    popped_query = query % (','.join(["'%s'" % i for i in ids]))
    
    pg_cur.execute(popped_query)

    to_construct = [r for r in pg_cur.fetchall()]
    return to_construct

def to_table(obs):
    samp_map = {}
    samp_count = 0
    obs_map = {}
    obs_count = 0
    to_load = {}

    for samp, obs, val in obs:
        if samp not in samp_map:
            samp_map[samp] = samp_count
            samp_count += 1
        if obs not in obs_map:
            obs_map[obs] = obs_count
            obs_count += 1
        samp_idx = samp_map[samp]
        obs_idx = obs_map[obs]

        to_load[(obs_idx, samp_idx)] = val

    samp_order = [i[0] for i in sorted(samp_map.items(), key=itemgetter(1))]
    obs_order = [i[0] for i in sorted(obs_map.items(), key=itemgetter(1))]

    return table_factory(to_load, samp_order, obs_order)

def main():
    pg_conn = psycopg2.connect('host=localhost')
    mongo_conn = pymongo.MongoClient('localhost', 27017)
    mongo_db = mongo_conn.prototype

    ids, recs = get_metadata(mongo_db, {})
    print len(ids)
    foo = fetch_all(pg_conn.cursor(), ids)
    print foo[:10]
    print foo[:10]
    print len(foo)

    table = to_table(foo)
    f = open('test.biom','w')
    f.write(table.getBiomFormatJsonString('asd'))
    f.close()

if __name__ == '__main__':
    main()
