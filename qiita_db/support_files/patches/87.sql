-- Aug 11, 2022
-- updating resource allocations to use slurm
UPDATE qiita.processing_job_resource_allocation SET allocation =
REPLACE(
  REPLACE(
    REPLACE(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(allocation, '-q qiita', '-p qiita'),
          '-l nodes=', '-N '),
        ':ppn=', ' -n '),
      '-l pmem=', '--mem-per-cpu '),
    '-l mem=', '--mem '),
  '-l walltime=', '--time '),
'-p 1023', '--qos=qiita_prio');

INSERT INTO qiita.filepath_type (filepath_type) VALUES ('bam');
