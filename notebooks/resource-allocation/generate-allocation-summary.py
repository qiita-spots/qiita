from qiita_db.software import Software
from subprocess import check_output
import pandas as pd
from io import StringIO
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.processing_job import ProcessingJob
from json import loads
from os.path import join


all_commands = [c for s in Software.iter(False) for c in s.commands]

# retrieving only the numerice external_id means that we are only focusing
# on barnacle2/slurm jobs
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
        # this will be raised if the study or the analysis has been deleted;
        # in other words, the processing_job was ran but the details about it
        # were erased when the user deleted them - however, we keep the job for
        # the record
        continue
    except TypeError as e:
        # similar to the except above, exept that for these 2 commands, we have
        # the study_id as None
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
    elif cmd.name == 'Validate':
        input_size = sum([len(x) for x in loads(
            j.parameters.values['files']).values()])
        sname = f"{sname} - {j.parameters.values['artifact_type']}"
    elif cmd.name == 'Alpha rarefaction curves [alpha_rarefaction]':
        extra_info = j.parameters.values[
            ('The number of rarefaction depths to include between min_depth '
             'and max_depth. (steps)')]

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

fn = join('/panfs', 'qiita', f'jobs_{df.Start.max()[:10]}.tsv.gz')
df.to_csv(fn, sep='\t', index=False)
