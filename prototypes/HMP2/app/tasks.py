from __future__ import absolute_import

from app.celery import celery
from celery import signature, group
from time import sleep
from json import dumps
from random import randint
from redis import Redis
from psycopg2 import connect as pg_connect

try:
    r_server = Redis()
except:
      raise RuntimeError("ERROR: unable to connect to the REDIS database.")

try:
    postgres = pg_connect("dbname='qiita' user='defaultuser' \
        password='defaultpassword' host='localhost'")
except:
    raise RuntimeError("ERROR: unable to connect to the POSTGRES database.")

@celery.task
def push_notification(user, job, analysis, msg, files=[], done=False):
    '''Creates JSON and takes care of push notification'''
    jsoninfo = {
        'job': job,
        'analysis': analysis,
        'msg': msg,
        'results': files,
    }
    if done:
        jsoninfo['done'] = 1
    else:
        jsoninfo['done'] = 0
    jsoninfo = dumps(jsoninfo)
    #need the rpush and publish for leaving page and if race condition
    try:
        r_server.rpush(user + ":messages", jsoninfo)
        r_server.publish(user, jsoninfo)
    except Exception, e:
        print "Can't push!\n", str(e), "\n", str(jsoninfo)


def finish_analysis(user, analysisname, analysisid, results):
    #wipe out all messages from redis list so no longer pushed to user
    for message in r_server.lrange(user+':messages', 0, -1):
        if '"analysis": "'+analysisname in str(message):
            r_server.lrem(user+':messages', message)
    #update job to done in job table
    pgcursor = postgres.cursor()
    SQL = "UPDATE qiita_analysis SET analysis_done = true WHERE analysis_id = %s"
    try:
        pgcursor.execute(SQL, (analysisid,))
        postgres.commit()
    except Exception, e:
        pgcursor.close()
        postgres.rollback()
        raise Exception("Can't finish off analysis!\n"+str(e)+\
            "\n"+SQL)
    #convert list of files to SQL formatted list
    for result in results:
        result[0] = "{"+','.join(result[0])+"}"
        result.append(str(analysisid))
    #update all analyses in analysis table to done and with their results
    SQL = "UPDATE qiita_job SET job_done = true, job_results = %s  WHERE \
    job_datatype = %s AND job_type = %s AND analysis_id = %s"
    try:
        pgcursor.executemany(SQL, results)
        postgres.commit()
        pgcursor.close()
    except Exception, e:
        pgcursor.close()
        postgres.rollback()
        for result in results:
            print SQL % result
        raise Exception("Can't finish off jobs!\n"+str(e))
    #finally, push finished state
    push_notification(user, analysisname, 'done', 'allcomplete')


@celery.task
def delete_job(user, jobid):
    try:
        pgcursor = postgres.cursor()
        pgcursor.execute('DELETE FROM qiita_job WHERE analysis_id = %s', 
            (jobid,))
        pgcursor.execute('DELETE FROM qiita_analysis WHERE analysis_id = %s', 
            (jobid,))
        postgres.commit()
        pgcursor.close()
    except Exception, e:
        postgres.rollback()
        raise Exception("Can't remove metaanalysis from database!\n"+str(e))


@celery.task
def switchboard(user, analysis_data):
    '''Fires off all analyses for a given job.

    INPUTS:
        user: username of user requesting job
        analysis_data: MetaAnalysisData object with all information in it.

    OUTPUT: NONE '''
    pgcursor = postgres.cursor()
    jobname = analysis_data.get_job()
    #insert analysis into the postgres analysis table
    SQL = '''INSERT INTO qiita_analysis (qiita_username, analysis_name, 
        analysis_studies, analysis_metadata, analysis_timestamp) VALUES 
        (%s, %s, %s, %s, 'now') RETURNING analysis_id'''
    try:
        pgcursor.execute(SQL, (user, jobname, 
            "{"+','.join(analysis_data.get_studies())+"}", 
            "{"+','.join(analysis_data.get_metadata())+"}"))
        jobid = pgcursor.fetchone()[0]
        postgres.commit()
    except Exception, e:
        postgres.rollback()
        raise Exception("Can't add metaanalysis to table!\n"+str(e)+\
            "\n"+SQL)

    #insert all jobs into jobs table
    SQL="INSERT INTO qiita_job (analysis_id,job_datatype,job_type,job_options) VALUES "
    for datatype in analysis_data.get_datatypes():
        for analysis in analysis_data.get_analyses(datatype):
            SQL += "(%i,'%s','%s','%s')," % (jobid, datatype, analysis, 
            dumps(analysis_data.get_options(datatype, analysis)))
    SQL = SQL[:-1]

    try:
        pgcursor.execute(SQL)
        postgres.commit()
        pgcursor.close()
    except Exception, e:
        postgres.rollback()
        print "Can't add metaanalysis jobs to table!\n"+str(e)+\
            "\n"+SQL

    #setup analysis
    analgroup = []
    for datatype in analysis_data.get_datatypes():
        for analysis in analysis_data.get_analyses(datatype):
            s = signature('app.tasks.'+analysis, args=(user, jobname, datatype,
                analysis_data.get_options(datatype, analysis)))
            analgroup.append(s)
    job = group(analgroup)
    res = job.apply_async()
    results = res.join()
    finish_analysis(user, jobname, jobid, results)


@celery.task
def OTU_Table(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':OTU_Table', 'Running')
    try:
        sleep(randint(1,5))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':OTU_Table', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':OTU_Table',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'OTU_Table']


@celery.task
def TopiaryExplorer_Visualization(user, jobname, datatype, opts):
    push_notification(user, jobname, 
        datatype + ':TopiaryExplorer_Visualization', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, 
            datatype + ':TopiaryExplorer_Visualization', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':TopiaryExplorer_Visualization',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'TopiaryExplorer_Visualization']


@celery.task
def Heatmap(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Heatmap', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':Heatmap', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Heatmap',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Heatmap']


@celery.task
def Heatmap(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Heatmap', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':Heatmap', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Heatmap',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Heatmap']


@celery.task
def Heatmap(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Heatmap', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':Heatmap', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Heatmap',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Heatmap']


@celery.task
def Taxonomy_Summary(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Taxonomy_Summary', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':Taxonomy_Summary', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Taxonomy_Summary',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Taxonomy_Summary']


@celery.task
def Alpha_Diversity(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Alpha_Diversity', 'Running')
    try:
        sleep(randint(5,10))
        results = ["static/demo/alpha/%s/alpha_rarefaction_plots/rarefaction_plots.html" % datatype.lower()]
        push_notification(user, jobname, datatype + ':Alpha_Diversity', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Alpha_Diversity',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Alpha_Diversity']


@celery.task
def Beta_Diversity(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Beta_Diversity', 'Running')
    try:
        sleep(randint(10,20))
        if datatype=="16S":
            results = ["static/demo/beta/emperor/unweighted_unifrac_16s/index.html", "static/demo/beta/emperor/weighted_unifrac_16s/index.html",]
        else:
            results = ["static/demo/beta/emperor/%s/index.html" % datatype.lower()]
        push_notification(user, jobname, datatype + ':Beta_Diversity', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Beta_Diversity',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Beta_Diversity']


@celery.task
def Procrustes(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Procrustes', 'Running')
    try:
        sleep(randint(20,20))
        results = ["static/demo/combined/plots/index.html"]
        push_notification(user, jobname, datatype + ':Procrustes', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Procrustes',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Procrustes']


@celery.task
def Network_Analysis(user, jobname, datatype, opts):
    push_notification(user, jobname, datatype + ':Network_Analysis', 'Running')
    try:
        sleep(randint(5,20))
        results = ["placeholder.html"]
        push_notification(user, jobname, datatype + ':Network_Analysis', 'Completed',
            results, done=True)
    except Exception, e:
        push_notification(user, jobname, datatype + ':Network_Analysis',
            'ERROR: ' + str(e), done=True)
    #MUST RETURN IN FORMAT (results, datatype, analysis)
    return [results, datatype, 'Network_Analysis']