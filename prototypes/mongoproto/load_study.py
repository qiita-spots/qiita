#!/usr/bin/env python

from sys import argv
from cogent.parse.fasta import MinimalFastaParser
from hashlib import md5
from collections import defaultdict
import psycopg2
import pymongo
import os
from biom.parse import parse_biom_table
import time
from gzip import open as gzopen

def bulk_load(table, filename, cur):
    curdir = os.getcwd()
    filename = os.path.join(curdir, filename)
    print "loading %s..." % filename
    try:
        cur.execute("copy %s from '%s' with delimiter as ','" % (table, filename))
    except Exception, e:
        print "failed to load %s" % filename
        raise e
    else:
        print "successfully loaded"

def parse_params(lines, study):
    # mocked
    ref = 'gg_13_5'
    similarity = 0.97
    trim = 'none'
    table_id = "%s:%s:%f:%s" % (study, ref, similarity, trim)
    return {'table_id':table_id,'study_id':study,'ref':ref,'similarity':similarity,'trim':trim}

def parse_mapping(f):
    lines = [l.strip().split('\t') for l in f]
    header = lines[0][:]
    header[0] = header[0][1:] # strip #
    header = map(lambda x: x.replace('.',''), header)
    
    for l in lines[1:]:
        yield {k:v for k,v in zip(header, l)} 

def timer(fn, *args):
    """Time the application of fn to args. Return (result, seconds).

    from http://norvig.com/python-iaq.html
    """
    start = time.clock()
    return fn(*args), time.clock() - start

def load_metadata(db, mapping):
    print "loading metadata..."
    to_load = []
    for rec in mapping:
        if db.metadata.find_one({'SampleID':rec['SampleID'], 'STUDY_ID':rec['STUDY_ID']}):
            raise ValueError, "Duplicate metadata records!"
        to_load.append(rec) 
    db.metadata.insert(to_load)

def main():
    pg_conn = psycopg2.connect('host=localhost')
    mongo_conn = pymongo.MongoClient('localhost', 27017)
    db = mongo_conn.prototype

    # check files
    # study_1742_split_library_seqs_and_mapping
    study_path = argv[1]
    study = study_path.split('_')[1]
    study_base = study_path.split('_split_library')[0]
    study_mapping = os.path.join(study_path, study_base + '_mapping_file.txt')
    study_biom = os.path.join(study_path, study_base + '_closed_reference_otu_table.biom')
    study_seqs = os.path.join(study_path, study_base + '_split_library_seqs.fna')

    if not os.path.exists(study_seqs):
        study_seqs += '.gz'
        if not os.path.exists(study_seqs):
            raise ValueError("Cannot find study sequences!")

    # loose sanity
    if db.metadata.find_one({'STUDY_ID':study}):
        raise ValueError("Study appears to already be loaded!")
    
    if study_seqs.endswith('.gz'):
        study_seqs = gzopen(study_seqs)
    else:
        study_seqs = open(study_seqs)

    study_biom = open(study_biom)
    study_mapping = parse_mapping(open(study_mapping))

    params = parse_params("mocked", study)

    print "load_metadata used time: %f" % timer(load_metadata, db, study_mapping)[1]
    print "load_sequence used time: %f" % timer(load_sequence, pg_conn, study_seqs, study)[1]
    print "load_otus used time: %f" % timer(load_otus, pg_conn, study_biom, params)[1]

def load_otus(conn, table, params):
    table = parse_biom_table(table)
    cur = conn.cursor()
    
    print "loading observations..."
    print "locking..."
    cur.execute('lock table observations')
    cur.execute('lock table observation_tables')

    cur.execute("insert into observation_tables values ('%s','%s','%s','%s',%f)" % (\
            params['table_id'],
            params['study_id'],
            params['ref'],
            params['trim'],
            params['similarity']))

    tableid = params['table_id']
    study = params['study_id']
    print "writing observations..."
    obs_fname = '%s_observations.csv' % study
    f = open(obs_fname, 'w')
    for values, sid, md in table.iterSamples(conv_to_np=False):
        study_sample = "%s::%s" % (study,sid)
        for (row, c_idx), val in values.items():
            f.write("%s,%s,%s,%f\n" % (tableid, study_sample, table.ObservationIds[c_idx], val))
    f.close()

    bulk_load("observations", obs_fname, cur)

    print "committing..."
    conn.commit()

    os.remove(obs_fname)

from StringIO import StringIO
def load_sequence(conn, to_read, study):
    print "loading sequences..."
    cur = conn.cursor()

    to_load_counts = defaultdict(int)
    to_load_seqs = StringIO()

    print "locking..."
    cur.execute('lock table sequence_hashes in ROW EXCLUSIVE mode')
    cur.execute('lock table sample_counts in ROW EXCLUSIVE mode')
    cur.execute('select seq_hash from sequence_hashes')
    seq_hashes = set([i[0] for i in cur.fetchall()])

    ### can reduce memory by storing to_load_counts in different buckets,
    ### can determine at runtime based on sample ids, e.g., randonly assign
    ### samples to N buckets. likely necessary for the global gut...

    new_seq_count = 0
    print "have %d hashes..." % len(seq_hashes)
    for id_, seq in MinimalFastaParser(to_read):
        study_sample = "%s::%s" % (study, id_.split('_', 1)[0])
        seq_md5 = md5(seq).hexdigest()
        if seq_md5 in seq_hashes:
            to_load_counts[(study_sample, seq_md5)] += 1
        else:
            seq_hashes.add(seq_md5)
            to_load_counts[(study_sample, seq_md5)] = 1
            to_load_seqs.write("%s,%s\n" % (seq_md5,seq))
            new_seq_count += 1
            
            # periodically write seqs
            if new_seq_count > 100000:
                to_load_seqs.seek(0)
                cur.copy_from(to_load_seqs, 'sequence_hashes', sep=',')
                conn.commit()
                to_load_seqs = StringIO()
                new_seq_count = 0
    
    # make sure to write when possible
    if new_seq_count:
        to_load_seqs.seek(0)
        cur.copy_from(to_load_seqs, 'sequence_hashes', sep=',')
        conn.commit()

    print "writing sample counts..."
    sample_seq_counts = StringIO()
    for (study_sample, seq_md5), count in to_load_counts.items():
        sample_seq_counts.write("%s,%s,%d\n" % (study_sample, seq_md5, count))
    
    print "Loading sample counts..."
    start = time.clock() 
    sample_seq_counts.seek(0)
    cur.copy_from(sample_seq_counts, "sample_counts", sep=',')
    conn.commit()
    print "New sample counts loaded in %f seconds" % (time.clock() - start)

    print "committing..."
    conn.commit()

if __name__ == '__main__':
    main()
