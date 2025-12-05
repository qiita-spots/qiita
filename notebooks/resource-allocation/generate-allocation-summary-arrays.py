import datetime
from io import StringIO
from os.path import join
from subprocess import check_output

import pandas as pd

from qiita_db.software import Software
from qiita_db.util import MaxRSS_helper

# This is an example script to collect the data we need from SLURM, the plan
# is that in the near future we will clean up and add these to the Qiita's main
# code and then have cronjobs to run them.

# at time of writting we have:
#     qp-spades spades
# (*) qp-woltka Woltka v0.1.4
#     qp-woltka SynDNA Woltka
#     qp-woltka Calculate Cell Counts
# (*) qp-meta Sortmerna v2.1b
# (*) qp-fastp-minimap2 Adapter and host filtering v2023.12
# ... and the admin plugin
# (*) qp-klp
# Here we are only going to create summaries for (*)


sacct = ["sacct", "-p", "--format=JobName,JobID,ElapsedRaw,MaxRSS,ReqMem", "-j"]
# for the non admin jobs, we will use jobs from the last six months
six_months = datetime.date.today() - datetime.timedelta(weeks=6 * 4)

print('The current "sofware - commands" that use job-arrays are:')
for s in Software.iter():
    if 'ENVIRONMENT="' in s.environment_script:
        for c in s.commands:
            print(f"{s.name} - {c.name}")

# 1. Command: woltka

fn = join("/panfs", "qiita", "jobs_woltka.tsv.gz")
print(f"Generating the summary for the woltka jobs: {fn}.")

cmds = [c for s in Software.iter(False) if "woltka" in s.name for c in s.commands]
jobs = [
    j
    for c in cmds
    for j in c.processing_jobs
    if j.status == "success" and j.heartbeat.date() > six_months and j.input_artifacts
]

data = []
for j in jobs:
    size = sum([fp["fp_size"] for fp in j.input_artifacts[0].filepaths])
    jid, mjid = j.external_id.strip().split()
    rvals = StringIO(check_output(sacct + [jid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    jmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    jwt = _d.ElapsedRaw.max()

    rvals = StringIO(check_output(sacct + [mjid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    mmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    mwt = _d.ElapsedRaw.max()

    data.append(
        {
            "jid": j.id,
            "sjid": jid,
            "mem": jmem,
            "wt": jwt,
            "type": "main",
            "db": j.parameters.values["Database"].split("/")[-1],
        }
    )
    data.append(
        {
            "jid": j.id,
            "sjid": mjid,
            "mem": mmem,
            "wt": mwt,
            "type": "merge",
            "db": j.parameters.values["Database"].split("/")[-1],
        }
    )
df = pd.DataFrame(data)
df.to_csv(fn, sep="\t", index=False)

# 2. qp-meta Sortmerna

fn = join("/panfs", "qiita", "jobs_sortmerna.tsv.gz")
print(f"Generating the summary for the woltka jobs: {fn}.")

# for woltka we will only use jobs from the last 6 months
cmds = [
    c for s in Software.iter(False) if "minimap2" in s.name.lower() for c in s.commands
]
jobs = [
    j
    for c in cmds
    for j in c.processing_jobs
    if j.status == "success" and j.heartbeat.date() > six_months and j.input_artifacts
]

data = []
for j in jobs:
    size = sum([fp["fp_size"] for fp in j.input_artifacts[0].filepaths])
    jid, mjid = j.external_id.strip().split()
    rvals = StringIO(check_output(sacct + [jid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    jmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    jwt = _d.ElapsedRaw.max()

    rvals = StringIO(check_output(sacct + [mjid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    mmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    mwt = _d.ElapsedRaw.max()

    data.append({"jid": j.id, "sjid": jid, "mem": jmem, "wt": jwt, "type": "main"})
    data.append({"jid": j.id, "sjid": mjid, "mem": mmem, "wt": mwt, "type": "merge"})
df = pd.DataFrame(data)
df.to_csv(fn, sep="\t", index=False)


# 3. Adapter and host filtering. Note that there is a new version deployed on
#    Jan 2024 so the current results will not be the most accurate

fn = join("/panfs", "qiita", "jobs_adapter_host.tsv.gz")
print(f"Generating the summary for the woltka jobs: {fn}.")

# for woltka we will only use jobs from the last 6 months
cmds = [c for s in Software.iter(False) if "meta" in s.name.lower() for c in s.commands]
jobs = [
    j
    for c in cmds
    if "sortmerna" in c.name.lower()
    for j in c.processing_jobs
    if j.status == "success" and j.heartbeat.date() > six_months and j.input_artifacts
]

data = []
for j in jobs:
    size = sum([fp["fp_size"] for fp in j.input_artifacts[0].filepaths])
    jid, mjid = j.external_id.strip().split()
    rvals = StringIO(check_output(sacct + [jid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    jmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    jwt = _d.ElapsedRaw.max()

    rvals = StringIO(check_output(sacct + [mjid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    mmem = _d.MaxRSS.apply(
        lambda x: x if type(x) is not str else MaxRSS_helper(x)
    ).max()
    mwt = _d.ElapsedRaw.max()

    data.append({"jid": j.id, "sjid": jid, "mem": jmem, "wt": jwt, "type": "main"})
    data.append({"jid": j.id, "sjid": mjid, "mem": mmem, "wt": mwt, "type": "merge"})
df = pd.DataFrame(data)
df.to_csv(fn, sep="\t", index=False)


# 4. The SPP!

fn = join("/panfs", "qiita", "jobs_spp.tsv.gz")
print(f"Generating the summary for the SPP jobs: {fn}.")

# for the SPP we will look at jobs from the last year
year = datetime.date.today() - datetime.timedelta(days=365)
cmds = [c for s in Software.iter(False) if s.name == "qp-klp" for c in s.commands]
jobs = [
    j
    for c in cmds
    for j in c.processing_jobs
    if j.status == "success" and j.heartbeat.date() > year
]

# for the SPP we need to find the jobs that were actually run, this means
# looping throught the existing slurm jobs and finding them
max_inter = 2000

data = []
for job in jobs:
    jei = int(job.external_id)
    rvals = StringIO(check_output(sacct + [str(jei)]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    mem = _d.MaxRSS.apply(lambda x: x if type(x) is not str else MaxRSS_helper(x)).max()
    wt = _d.ElapsedRaw.max()
    # the current "easy" way to determine if amplicon or other is to check
    # the file extension of the filename
    stype = "other"
    if job.parameters.values["sample_sheet"]["filename"].endswith(".txt"):
        stype = "amplicon"
    rid = job.parameters.values["run_identifier"]
    data.append(
        {
            "jid": job.id,
            "sjid": jei,
            "mem": mem,
            "stype": stype,
            "wt": wt,
            "type": "main",
            "rid": rid,
            "name": _d.JobName[0],
        }
    )

    # let's look for the convert job
    for jid in range(jei + 1, jei + max_inter):
        rvals = StringIO(check_output(sacct + [str(jid)]).decode("ascii"))
        _d = pd.read_csv(rvals, sep="|")
        if [1 for x in _d.JobName.values if x.startswith(job.id)]:
            cjid = int(_d.JobID[0])
            mem = _d.MaxRSS.apply(
                lambda x: x if type(x) is not str else MaxRSS_helper(x)
            ).max()
            wt = _d.ElapsedRaw.max()

            data.append(
                {
                    "jid": job.id,
                    "sjid": cjid,
                    "mem": mem,
                    "stype": stype,
                    "wt": wt,
                    "type": "convert",
                    "rid": rid,
                    "name": _d.JobName[0],
                }
            )

            # now let's look for the next step, if amplicon that's fastqc but
            # if other that's qc/nuqc
            for jid in range(cjid + 1, cjid + max_inter):
                rvals = StringIO(check_output(sacct + [str(jid)]).decode("ascii"))
                _d = pd.read_csv(rvals, sep="|")
                if [1 for x in _d.JobName.values if x.startswith(job.id)]:
                    qc_jid = _d.JobIDRaw.apply(lambda x: int(x.split(".")[0])).max()
                    qcmem = _d.MaxRSS.apply(
                        lambda x: x if type(x) is not str else MaxRSS_helper(x)
                    ).max()
                    qcwt = _d.ElapsedRaw.max()

                    if stype == "amplicon":
                        data.append(
                            {
                                "jid": job.id,
                                "sjid": qc_jid,
                                "mem": qcmem,
                                "stype": stype,
                                "wt": qcwt,
                                "type": "fastqc",
                                "rid": rid,
                                "name": _d.JobName[0],
                            }
                        )
                    else:
                        data.append(
                            {
                                "jid": job.id,
                                "sjid": qc_jid,
                                "mem": qcmem,
                                "stype": stype,
                                "wt": qcwt,
                                "type": "qc",
                                "rid": rid,
                                "name": _d.JobName[0],
                            }
                        )
                        for jid in range(qc_jid + 1, qc_jid + max_inter):
                            rvals = StringIO(
                                check_output(sacct + [str(jid)]).decode("ascii")
                            )
                            _d = pd.read_csv(rvals, sep="|")
                            if [1 for x in _d.JobName.values if x.startswith(job.id)]:
                                fqc_jid = _d.JobIDRaw.apply(
                                    lambda x: int(x.split(".")[0])
                                ).max()
                                fqcmem = _d.MaxRSS.apply(
                                    lambda x: x
                                    if type(x) is not str
                                    else MaxRSS_helper(x)
                                ).max()
                                fqcwt = _d.ElapsedRaw.max()
                                data.append(
                                    {
                                        "jid": job.id,
                                        "sjid": fqc_jid,
                                        "mem": fqcmem,
                                        "stype": stype,
                                        "wt": fqcwt,
                                        "type": "fastqc",
                                        "rid": rid,
                                        "name": _d.JobName[0],
                                    }
                                )
                                break
                    break
            break

df = pd.DataFrame(data)
df.to_csv(fn, sep="\t", index=False)
