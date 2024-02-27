-- Jan 9, 2024
-- add control of max artifacts in analysis to the settings
--    using 35 as default considering that a core div creates ~17 so allowing
--    for 2 of those + 1
ALTER TABLE settings
  ADD COLUMN IF NOT EXISTS max_artifacts_in_workflow INT DEFAULT 35;
