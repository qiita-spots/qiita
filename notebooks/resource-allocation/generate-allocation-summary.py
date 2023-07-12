
from qiita_db.software import Software
from subprocess import check_output
import pandas as pd
from io import StringIO
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.artifact import Artifact
from qiita_db.analysis import Analysis
from qiita_db.processing_job import ProcessingJob
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from json import loads
from datetime import datetime

all_commands = [c for s in Software.iter(False) for c in s.commands]
main_jobs = [j for c in all_commands for j in c.processing_jobs
             if j.status == 'success' and j.external_id.isnumeric()]

sacct = ['sacct', '-p', '--format=JobID,ElapsedRaw,MaxRSS,Submit,Start,MaxRSS,'
         'CPUTimeRAW,ReqMem,AllocCPUs,AveVMSize', '-j']

data = []
for i, j in enumerate(main_jobs):
    if i % 1000 == 0:
        print(f'{i}/{len(main_jobs)}')
    eid = j.external_id
    extra_info = ''
    rvals = StringIO(check_output(sacct + [eid]).decode('ascii'))
    _d = pd.read_csv(rvals, sep='|')
    _d['QiitaID'] = j.id
    cmd = j.command
    s = j.command.software
    try:
        samples, columns, input_size = j.shape
    except QiitaDBUnknownIDError:
        continue
    except TypeError as e:
        if cmd.name in {'create_sample_template', 'delete_sample_template'}:
            continue
        else:
            raise e

    sname = s.name

    if cmd.name == 'release_validators':
        ej = ProcessingJob(j.parameters.values['job'])
        extra_info = ej.command.name
        samples, columns, input_size = ej.shape
    elif cmd.name == 'complete_job':
        artifacts = loads(j.parameters.values['payload'])['artifacts']
        if artifacts is not None:
            extra_info = ','.join({
                x['artifact_type'] for x in artifacts.values()
                if 'artifact_type' in x})
    elif cmd.name == 'delete_sample_or_column':
        v = j.parameters.values
        try:
            if v['obj_class'] == 'SampleTemplate':
                obj = SampleTemplate(v['obj_id'])
            else:
                obj = PrepTemplate(v['obj_id'])
        except QiitaDBUnknownIDError:
            continue
        samples = len(obj)
    elif cmd.name == 'build_analysis_files':
        analysis = Analysis(j.parameters.values['analysis'])
        extra_info = sum([fp['fp_size']
                          for x in analysis.samples.keys()
                          for fp in Artifact(x).filepaths
                          if fp['fp_type'] == 'biom'])
        columns = j.parameters.values['categories']
        if columns is not None:
            columns = len(j.parameters.values['categories'])
    elif cmd.name == 'Sequence Processing Pipeline':
        body = j.parameters.values['sample_sheet']['body']
        extra_info = body.count('\r')
        ei = body.count('\n')
        if ei > extra_info:
            extra_info = ei
        extra_info = f'({extra_info}, {body.startswith("sample_name")})'
    elif cmd.name == 'Validate':
        input_size = sum([len(x) for x in loads(
            j.parameters.values['files']).values()])
        sname = f"{sname} - {j.parameters.values['artifact_type']}"
    elif cmd.name == 'Alpha rarefaction curves [alpha_rarefaction]':
        extra_info = j.parameters.values[
            ('The maximum rarefaction depth. Must be greater than min_depth. '
             '(max_depth)')]

    _d['external_id'] = eid
    _d['sId'] = s.id
    _d['sName'] = sname
    _d['sVersion'] = s.version
    _d['cId'] = cmd.id
    _d['cName'] = cmd.name
    _d['samples'] = samples
    _d['columns'] = columns
    _d['input_size'] = input_size
    _d['extra_info'] = extra_info
    _d.drop(columns=['Unnamed: 10'], inplace=True)
    data.append(_d)

df = pd.concat(data)

df.to_csv(
    f'/panfs/qiita/job_stats_{datetime.now().strftime("%m%d%y")}.tsv.gz',
    sep='\t', index=False)
