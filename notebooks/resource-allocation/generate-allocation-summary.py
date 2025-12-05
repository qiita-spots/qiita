from datetime import datetime, timedelta
from io import StringIO
from json import loads
from os.path import join
from subprocess import check_output

import pandas as pd

from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Software
from qiita_db.util import MaxRSS_helper

all_commands = [c for s in Software.iter(False) for c in s.commands]

# retrieving only the numerice external_id means that we are only focusing
# on barnacle2/slurm jobs
main_jobs = [
    j
    for c in all_commands
    for j in c.processing_jobs
    if j.status == "success" and j.external_id.isnumeric()
]

sacct = [
    "sacct",
    "-p",
    "--format=JobID,ElapsedRaw,MaxRSS,Submit,Start,MaxRSS,"
    "CPUTimeRAW,ReqMem,AllocCPUs,AveVMSize",
    "-j",
]

data = []
for i, j in enumerate(main_jobs):
    if i % 1000 == 0:
        print(f"{i}/{len(main_jobs)}")
    eid = j.external_id
    extra_info = ""
    rvals = StringIO(check_output(sacct + [eid]).decode("ascii"))
    _d = pd.read_csv(rvals, sep="|")
    _d["QiitaID"] = j.id
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
        if cmd.name in {
            "create_sample_template",
            "delete_sample_template",
            "list_remote_files",
        }:
            continue
        else:
            raise e

    sname = s.name

    if cmd.name == "release_validators":
        ej = ProcessingJob(j.parameters.values["job"])
        extra_info = ej.command.name
        samples, columns, input_size = ej.shape
    elif cmd.name == "complete_job":
        artifacts = loads(j.parameters.values["payload"])["artifacts"]
        if artifacts is not None:
            extra_info = ",".join(
                {x["artifact_type"] for x in artifacts.values() if "artifact_type" in x}
            )
    elif cmd.name == "Validate":
        input_size = sum([len(x) for x in loads(j.parameters.values["files"]).values()])
        sname = f"{sname} - {j.parameters.values['artifact_type']}"
    elif cmd.name == "Alpha rarefaction curves [alpha_rarefaction]":
        extra_info = j.parameters.values[
            (
                "The number of rarefaction depths to include between min_depth "
                "and max_depth. (steps)"
            )
        ]

    _d["external_id"] = eid
    _d["sId"] = s.id
    _d["sName"] = sname
    _d["sVersion"] = s.version
    _d["cId"] = cmd.id
    _d["cName"] = cmd.name
    _d["samples"] = samples
    _d["columns"] = columns
    _d["input_size"] = input_size
    _d["extra_info"] = extra_info
    _d.drop(columns=["Unnamed: 10"], inplace=True)
    data.append(_d)

data = pd.concat(data)

# In slurm, each JobID is represented by 3 rows in the dataframe:
#   - external_id:  overall container for the job and its associated
#                   requests. When the Timelimit is hit, the container
#                   would take care of completing/stopping the
#                   external_id.batch job.
#   - external_id.batch: it's a container job, it provides how
#                        much memory it uses and cpus allocated, etc.
#   - external_id.extern: takes into account anything that happens
#                         outside processing but yet is included in
#                         the container resources. As in, if you ssh
#                         to the node and do something additional or run
#                         a prolog script, that processing would be under
#                         external_id but separate from external_id.batch.
# Here we are going to merge all this info into a single row + some
# other columns
date_fmt = "%Y-%m-%dT%H:%M:%S"

df = []
for eid, __df in data.groupby("external_id"):
    tmp = __df.iloc[1].copy()
    # Calculating WaitTime, basically how long did the job took to start
    # this is useful for some general profiling
    tmp["WaitTime"] = datetime.strptime(
        __df.iloc[0].Start, date_fmt
    ) - datetime.strptime(__df.iloc[0].Submit, date_fmt)
    df.append(tmp)
df = pd.DataFrame(df)

# This is important as we are transforming the MaxRSS to raw value
# so we need to confirm that there is no other suffixes
print("Make sure that only 0/K/M exist", set(df.MaxRSS.apply(lambda x: str(x)[-1])))

# Generating new columns
df["MaxRSSRaw"] = df.MaxRSS.apply(lambda x: MaxRSS_helper(str(x)))
df["ElapsedRawTime"] = df.ElapsedRaw.apply(lambda x: timedelta(seconds=float(x)))

# Thu, Apr 27, 2023 was the first time Jeff and I changed the old allocations
# (from barnacle) to a better allocation so using job 1265533 as the
# before/after so we only use the latests for the newest version
df["updated"] = df.external_id.apply(
    lambda x: "after" if int(x) >= 1265533 else "before"
)

fn = join("/panfs", "qiita", f"jobs_{df.Start.max()[:10]}.tsv.gz")
df.to_csv(fn, sep="\t", index=False)
