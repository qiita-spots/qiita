-- Jan 27, 2017
-- sequeneces -> sequences

UPDATE qiita.artifact_type SET description = 'Demultiplexed and QC sequences'
  WHERE artifact_type = 'Demultiplexed'
    AND description = 'Demultiplexed and QC sequeneces';
