import pandas as pd

# Example data loading
filename = './data/jobs_2024-02-21.tsv.gz'
df = pd.read_csv(filename, sep='\t', dtype={'extra_info': str})

# Convert string to timedelta, then to total seconds
df['ElapsedRawTime'] = pd.to_timedelta(
                                       df['ElapsedRawTime']).apply(
                                        lambda x: x.total_seconds())

cname = "Validate"
sname = "Diversity types - alpha_vector"
df = df[(df.cName == cname) & (df.sName == sname)]

df['samples'] = df['samples'].fillna(0).astype(int)
df['columns'] = df['columns'].fillna(0).astype(int)
df['input_size'] = df['input_size'].fillna(0).astype(int)
df['MaxRSSRaw'] = df['MaxRSSRaw'].fillna(0).astype(int)
df['ElapsedRawTime'] = df['ElapsedRawTime'].fillna(0).astype(int)

COL_NAME = 'samples * columns'
df[COL_NAME] = df['samples'] * df['columns']
columns = ["MaxRSSRaw", "ElapsedRawTime"]
max_rows = []

for curr in columns:
    # Get the maximum value for 'curr' within each COL_NAME group
    max_values = df.groupby(COL_NAME)[curr].transform(max)
    # Filter rows where the current column's value
    # is the maximum within its group
    curr_rows = df[df[curr] == max_values]
    max_rows.append(curr_rows)

filtered_df = pd.concat(max_rows).drop_duplicates().reset_index(drop=True)

# INSERT INTO qiita.processing_job(processing_job_id, email, command_id,
# command_parameters, processing_job_status_id)
# VALUES('ca27ddbc-a678-4b09-8a1d-b65f52f8eb49',
# 'admin@foo.com', 1, '""'::json, 1);

# INSERT INTO qiita.slurm_resource_allocations(processing_job_id, samples,
# columns, input_size, extra_info, memory_used, walltime_used)
# VALUES('ca27ddbc-a678-4b09-8a1d-b65f52f8eb49', 39, 81, 2, 'nan',
# 327036000, 91);

# processing_job_id    uuid  NOT NULL,
# samples              integer,
# columns              integer,
# input_size           bigint,
# extra_info           varchar DEFAULT NULL,
# memory_used          bigint,
# walltime_used        integer,

res = ""

for index, row in filtered_df.iterrows():
    res += f"""('{row['QiitaID']}', 'admin@foo.bar', 1, '""'::json, 1),\n"""
res += ";\n"
res += "Split\n"
for index, row in filtered_df.iterrows():
    res += (
        f"('{row['QiitaID']}', {int(row['samples'])}, "
        f"{int(row['columns'])}, {int(row['input_size'])}, "
        f"'{row['extra_info']}', {int(row['MaxRSSRaw'])}, "
        f"{int(row['ElapsedRawTime'])}),\n"
    )

res += ";\n"

with open("sql.txt", 'w') as filename:
    filename.write(res)
