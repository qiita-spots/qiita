-- Adding 3 studies and their sample-metadata to test qp-knight-lab-processing pluing
INSERT INTO
    qiita.study (
        study_id,
        email,
        timeseries_type_id,
        metadata_complete,
        mixs_compliant,
        principal_investigator_id,
        reprocess,
        study_title,
        study_alias,
        study_description,
        study_abstract
    )
VALUES
    (
        6123,
        'demo@microbio.me',
        1,
        true,
        true,
        1,
        false,
        'Study 6123',
        '',
        '',
        ''
    ),
    (
        11661,
        'demo@microbio.me',
        1,
        true,
        true,
        1,
        false,
        'Study 11661',
        '',
        '',
        ''
    ),
    (
        13059,
        'demo@microbio.me',
        1,
        true,
        true,
        1,
        false,
        'Study 13059',
        '',
        '',
        ''
    );

-- Add studies to Qiita portal
INSERT INTO qiita.study_portal (study_id, portal_type_id) VALUES (6123, 1), (11661, 1), (13059, 1);

-- Creating the sample-metadata for tne new studies
CREATE TABLE qiita.sample_6123 (
    sample_id VARCHAR NOT NULL PRIMARY KEY,
    sample_values JSONB NOT NULL
);
INSERT INTO qiita.sample_6123 (sample_id, sample_values) VALUES  ('qiita_sample_column_names', '{}'::json);
CREATE TABLE qiita.sample_11661 (
    sample_id VARCHAR NOT NULL PRIMARY KEY,
    sample_values JSONB NOT NULL
);
INSERT INTO qiita.sample_11661 (sample_id, sample_values) VALUES  ('qiita_sample_column_names', '{}'::json);
CREATE TABLE qiita.sample_13059 (
    sample_id VARCHAR NOT NULL PRIMARY KEY,
    sample_values JSONB NOT NULL
);
INSERT INTO qiita.sample_13059 (sample_id, sample_values) VALUES  ('qiita_sample_column_names', '{}'::json);

-- Now adding the samples
INSERT INTO
    qiita.study_sample (study_id, sample_id)
VALUES
    -- 11661
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-143'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-144'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-145'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-146'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-147'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-148'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-149'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-150'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-151'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-152'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-153'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-154'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-155'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-156'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-157'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-158'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-159'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-160'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-161'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-162'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-163'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-164'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-165'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-166'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-167'),
    (11661, '11661.CDPH-SAL.Salmonella.Typhi.MDL-168'),
    (11661, '11661.P21.E.coli.ELI344'),
    (11661, '11661.P21.E.coli.ELI345'),
    (11661, '11661.P21.E.coli.ELI347'),
    (11661, '11661.P21.E.coli.ELI348'),
    (11661, '11661.P21.E.coli.ELI349'),
    (11661, '11661.P21.E.coli.ELI350'),
    (11661, '11661.P21.E.coli.ELI351'),
    (11661, '11661.P21.E.coli.ELI352'),
    (11661, '11661.P21.E.coli.ELI353'),
    (11661, '11661.P21.E.coli.ELI354'),
    (11661, '11661.P21.E.coli.ELI355'),
    (11661, '11661.P21.E.coli.ELI357'),
    (11661, '11661.P21.E.coli.ELI358'),
    (11661, '11661.P21.E.coli.ELI359'),
    (11661, '11661.P21.E.coli.ELI361'),
    (11661, '11661.P21.E.coli.ELI362'),
    (11661, '11661.P21.E.coli.ELI363'),
    (11661, '11661.P21.E.coli.ELI364'),
    (11661, '11661.P21.E.coli.ELI365'),
    (11661, '11661.P21.E.coli.ELI366'),
    (11661, '11661.P21.E.coli.ELI367'),
    (11661, '11661.P21.E.coli.ELI368'),
    (11661, '11661.P21.E.coli.ELI369'),
    (11661, '11661.stALE.E.coli.A1.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A2.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A3.F18.I1.R1'),
    (11661, '11661.stALE.E.coli.A3.F40.I1.R1'),
    (11661, '11661.stALE.E.coli.A4.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A4.F21.I1.R2'),
    (11661, '11661.stALE.E.coli.A4.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A5.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A5.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A6.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A6.F43.I1.R1'),
    (11661, '11661.stALE.E.coli.A7.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A7.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A8.F20.I1.R1'),
    (11661, '11661.stALE.E.coli.A8.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A9.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A9.F44.I1.R1'),
    (11661, '11661.stALE.E.coli.A10.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A10.F43.I1.R1'),
    (11661, '11661.stALE.E.coli.A10.F131.I1.R1'),
    (11661, '11661.stALE.E.coli.A11.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A11.F43.I1.R1'),
    (11661, '11661.stALE.E.coli.A11.F119.I1.R1'),
    (11661, '11661.stALE.E.coli.A12.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A12.F43.I1.R1'),
    (11661, '11661.stALE.E.coli.A12.F136.I1.R1'),
    (11661, '11661.stALE.E.coli.A13.F20.I1.R1'),
    (11661, '11661.stALE.E.coli.A13.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A13.F121.I1.R1'),
    (11661, '11661.stALE.E.coli.A14.F20.I1.R1'),
    (11661, '11661.stALE.E.coli.A14.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A14.F133.I1.R1'),
    (11661, '11661.stALE.E.coli.A15.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A15.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A15.F117.I1.R1'),
    (11661, '11661.stALE.E.coli.A16.F20.I1.R1'),
    (11661, '11661.stALE.E.coli.A16.F42.I1.R1'),
    (11661, '11661.stALE.E.coli.A16.F134.I1.R1'),
    (11661, '11661.stALE.E.coli.A17.F21.I1.R1'),
    (11661, '11661.stALE.E.coli.A17.F118.I1.R1'),
    (11661, '11661.stALE.E.coli.A18.F18.I1.R1'),
    (11661, '11661.stALE.E.coli.A18.F39.I1.R1'),
    (11661, '11661.stALE.E.coli.A18.F130.I1.R1'),
    (11661, '11661.BLANK.40.12G'),
    (11661, '11661.BLANK.40.12H'),
    (11661, '11661.Pputida.JBEI.HGL.Pputida.107.BP6'),
    (11661, '11661.Pputida.JBEI.HGL.Pputida.108.BP7'),
    (11661, '11661.Pputida.JBEI.HGL.Pputida.109.BP8'),
    (11661, '11661.Pputida.JBEI.HGL.Pputida.110.M2'),
    (11661, '11661.Pputida.JBEI.HGL.Pputida.111.M5'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.112'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.113'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.114'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.115'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.116'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.117'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.118'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.119'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.120'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.121'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.122'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.123'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.124'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.125'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.126'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.127'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.128'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.129'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.130'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.131'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.132'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.133'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.134'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.135'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.136'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.137'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.138'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.139'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.140'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.141'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.142'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.143'),
    (11661, '11661.Pputida.TALE.HGL.Pputida.144'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.145'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.146'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.147'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.148'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.149'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.150'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.151'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.152'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.153'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.154'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.155'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.156'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.157'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.158'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.159'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.160'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.161'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.162'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.163'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.164'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.165'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.166'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.167'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.168'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.169'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.170'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.171'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.172'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.173'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.174'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.175'),
    (11661, '11661.Pputida.PALE.HGL.Pputida.176'),
    (11661, '11661.JM-Metabolic.GN0.2005'),
    (11661, '11661.JM-Metabolic.GN0.2007'),
    (11661, '11661.JM-Metabolic.GN0.2009'),
    (11661, '11661.JM-Metabolic.GN0.2094'),
    (11661, '11661.JM-Metabolic.GN0.2099'),
    (11661, '11661.JM-Metabolic.GN0.2148'),
    (11661, '11661.JM-Metabolic.GN0.2165'),
    (11661, '11661.JM-Metabolic.GN0.2169'),
    (11661, '11661.JM-Metabolic.GN0.2172'),
    (11661, '11661.JM-Metabolic.GN0.2175'),
    (11661, '11661.JM-Metabolic.GN0.2183'),
    (11661, '11661.JM-Metabolic.GN0.2215'),
    (11661, '11661.JM-Metabolic.GN0.2254'),
    (11661, '11661.JM-Metabolic.GN0.2277'),
    (11661, '11661.JM-Metabolic.GN0.2290'),
    (11661, '11661.JM-Metabolic.GN0.2337'),
    (11661, '11661.JM-Metabolic.GN0.2317'),
    (11661, '11661.JM-Metabolic.GN0.2354'),
    (11661, '11661.JM-Metabolic.GN0.2375'),
    (11661, '11661.JM-Metabolic.GN0.2380'),
    (11661, '11661.JM-Metabolic.GN0.2393'),
    (11661, '11661.JM-Metabolic.GN0.2404'),
    (11661, '11661.BLANK.41.12H'),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.4.14'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.4.23'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.4.48'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.6.21'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.6.35'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.10.13'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.10.28'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.BOP27.10.51'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.18.19'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.18.59'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.18.35'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.20.16'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.20.43'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.20.71'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.22.16'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.22.28'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.22.52'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.24.9'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.24.24'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.24.52'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.26.6'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.26.27'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.26.69'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.28.13'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.28.28'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.28.53'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.30.7'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.30.22'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.30.60'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.32.6'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.32.20'
    ),
    (
        11661,
        '11661.Deoxyribose.PALE.ALE.MG1655.Lib4.32.56'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.1.24'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.1.57'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.1.69'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.3.23'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.3.50'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.3.61'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.5.22'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.5.36'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.5.46'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.7.23'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.7.41'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.7.51'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.17.25'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.17.58'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.17.64'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.19.25'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.19.55'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.19.63'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.21.23'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.21.46'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.21.51'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.29.25'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.29.49'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.29.57'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.31.24'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.31.42'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.31.62'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.33.21'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.33.41'
    ),
    (
        11661,
        '11661.AB5075.AZM.TALE.in.MHB.A.baumannii.AB5075.WT.33.50'
    ),
    (11661, '11661.JM-Metabolic.GN02514'),
    (11661, '11661.JM-Metabolic.GN02529'),
    (11661, '11661.JM-Metabolic.GN02531'),
    (11661, '11661.JM-Metabolic.GN02567'),
    (11661, '11661.JM-Metabolic.GN02590'),
    (11661, '11661.JM-Metabolic.GN02657'),
    (11661, '11661.JM-Metabolic.GN02748'),
    (11661, '11661.JM-Metabolic.GN02766'),
    (11661, '11661.JM-Metabolic.GN02769'),
    (11661, '11661.JM-Metabolic.GN02787'),
    (11661, '11661.JM-Metabolic.GN03132'),
    (11661, '11661.JM-Metabolic.GN03218'),
    (11661, '11661.JM-Metabolic.GN03252'),
    (11661, '11661.JM-Metabolic.GN03409'),
    (11661, '11661.JM-Metabolic.GN04014'),
    (11661, '11661.JM-Metabolic.GN04094'),
    (11661, '11661.JM-Metabolic.GN04255'),
    (11661, '11661.JM-Metabolic.GN04306'),
    (11661, '11661.JM-Metabolic.GN04428'),
    (11661, '11661.JM-Metabolic.GN04488'),
    (11661, '11661.JM-Metabolic.GN04540'),
    (11661, '11661.JM-Metabolic.GN04563'),
    (11661, '11661.JM-Metabolic.GN04612'),
    (11661, '11661.JM-Metabolic.GN04665'),
    (11661, '11661.JM-Metabolic.GN04682'),
    (11661, '11661.JM-Metabolic.GN05002'),
    (11661, '11661.JM-Metabolic.GN05109'),
    (11661, '11661.JM-Metabolic.GN05128'),
    (11661, '11661.JM-Metabolic.GN05367'),
    (11661, '11661.JM-Metabolic.GN05377'),
    (11661, '11661.BLANK.42.12G'),
    (11661, '11661.BLANK.42.12H'),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0326'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0327'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0328'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0329'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0330'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0352'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0353'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0354'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0355'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0356'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0357'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0364'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0366'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0367'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0368'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0369'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0370'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0371'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0372'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0373'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0374'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0375'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0376'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0377'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0378'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0380'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0381'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0382'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0383'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0384'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0385'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0386'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0387'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0388'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0389'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0390'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0391'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0392'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0393'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0394'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0395'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0396'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0397'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0398'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0399'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0400'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0401'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0402'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0403'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0404'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0405'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0406'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0407'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0408'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0409'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0417'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0418'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0419'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0420'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0421'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0473'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0474'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0483'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0484'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0485'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0486'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0516'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0517'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0518'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0519'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0520'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0521'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0522'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0523'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0524'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-B0525'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R08624'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R08704'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R10727'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11044'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11078'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11101'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11102'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11103'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11135'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11153'
    ),
    (
        11661,
        '11661.JM-MEC.Staphylococcus.aureusstrain.BERTI-R11154'
    ),
    (11661, '11661.JM-Metabolic.GN02424'),
    (11661, '11661.JM-Metabolic.GN02446'),
    (11661, '11661.JM-Metabolic.GN02449'),
    (11661, '11661.JM-Metabolic.GN02487'),
    (11661, '11661.JM-Metabolic.GN02501'),
    (11661, '11661.BLANK.43.12G'),
    (11661, '11661.BLANK.43.12H'),
    (11661, '11661.RMA.KHP.rpoS.Mage.Q97D'),
    (11661, '11661.RMA.KHP.rpoS.Mage.Q97L'),
    (11661, '11661.RMA.KHP.rpoS.Mage.Q97N'),
    (11661, '11661.RMA.KHP.rpoS.Mage.Q97E'),
    (11661, '11661.JBI.KHP.HGL.021'),
    (11661, '11661.JBI.KHP.HGL.022'),
    (11661, '11661.JBI.KHP.HGL.023'),
    (11661, '11661.JBI.KHP.HGL.024'),
    (11661, '11661.JBI.KHP.HGL.025'),
    (11661, '11661.JBI.KHP.HGL.026'),
    (11661, '11661.JBI.KHP.HGL.027'),
    (11661, '11661.JBI.KHP.HGL.028.Amitesh.soxR'),
    (11661, '11661.JBI.KHP.HGL.029.Amitesh.oxyR'),
    (11661, '11661.JBI.KHP.HGL.030.Amitesh.soxR.oxyR'),
    (11661, '11661.JBI.KHP.HGL.031.Amitesh.rpoS'),
    -- 6123
    (6123, '6123.3A'),
    (6123, '6123.4A'),
    (6123, '6123.5B'),
    (6123, '6123.6A'),
    (6123, '6123.BLANK.41.12G'),
    (6123, '6123.7A'),
    (6123, '6123.8A'),
    (6123, '6123.ISB'),
    (6123, '6123.GFR');

-- 'BMS': [('BMS', 'BMS.BLANK1.1A'), ('BMS', 'BMS.BLANK1.1B'), ('BMS', 'BMS.BLANK1.1C'), ('BMS', 'BMS.BLANK1.1D'), ('BMS', 'BMS.BLANK1.1E'), ('BMS', 'BMS.BLANK1.1F'), ('BMS', 'BMS.BLANK1.1G'), ('BMS', 'BMS.BLANK1.1H'), ('BMS', 'BMS.AP581451B02'), ('BMS', 'BMS.EP256645B01'), ('BMS', 'BMS.EP112567B02'), ('BMS', 'BMS.EP337425B01'), ('BMS', 'BMS.LP127890A01'), ('BMS', 'BMS.EP159692B04'), ('BMS', 'BMS.EP987683A01'), ('BMS', 'BMS.AP959450A03'), ('BMS', 'BMS.SP464350A04'), ('BMS', 'BMS.C9'), ('BMS', 'BMS.ep256643b01'), ('BMS', 'BMS.EP121011B-1'), ('BMS', 'BMS.AP616837B04'), ('BMS', 'BMS.SP506933A04'), ('BMS', 'BMS.EP159695B01'), ('BMS', 'BMS.EP256644B01'), ('BMS', 'BMS.SP511289A02'), ('BMS', 'BMS.EP305735B04'), ('BMS', 'BMS.SP415030A01'), ('BMS', 'BMS.AP549681B02'), ('BMS', 'BMS.AP549678B01'), ('BMS', 'BMS.EP260544B04'), ('BMS', 'BMS.EP202452B01'), ('BMS', 'BMS.EP282276B04'), ('BMS', 'BMS.SP531696A04'), ('BMS', 'BMS.SP515443A04'), ('BMS', 'BMS.SP515763A04'), ('BMS', 'BMS.EP184255B04'), ('BMS', 'BMS.SP503615A02'), ('BMS', 'BMS.EP260543B04'), ('BMS', 'BMS.EP768748A04'), ('BMS', 'BMS.AP309872B03'), ('BMS', 'BMS.AP568785B04'), ('BMS', 'BMS.EP721390A04'), ('BMS', 'BMS.EP940013A01'), ('BMS', 'BMS.EP291979B04'), ('BMS', 'BMS.EP182065B04'), ('BMS', 'BMS.EP128904B02'), ('BMS', 'BMS.EP915769A04'), ('BMS', 'BMS.SP464352A03'), ('BMS', 'BMS.SP365864A04'), ('BMS', 'BMS.SP511294A04'), ('BMS', 'BMS.EP061002B01'), ('BMS', 'BMS.SP410793A01'), ('BMS', 'BMS.SP232077A04'), ('BMS', 'BMS.EP128910B01'), ('BMS', 'BMS.AP531397B04'), ('BMS', 'BMS.EP043583B01'), ('BMS', 'BMS.EP230245B01'), ('BMS', 'BMS.EP606652B04'), ('BMS', 'BMS.EP207041B01'), ('BMS', 'BMS.EP727972A04'), ('BMS', 'BMS.EP291980B04'), ('BMS', 'BMS.EP087938B02'), ('BMS', 'BMS.SP471496A04'), ('BMS', 'BMS.SP573823A04'), ('BMS', 'BMS.EP393718B01'), ('BMS', 'BMS.SP612496A01'), ('BMS', 'BMS.EP032410B02'), ('BMS', 'BMS.EP073216B01'), ('BMS', 'BMS.EP410046B01'), ('BMS', 'BMS.SP561451A04'), ('BMS', 'BMS.EP320438B01'), ('BMS', 'BMS.SP612495A04'), ('BMS', 'BMS.EP446604B03'), ('BMS', 'BMS.EP446602B-1'), ('BMS', 'BMS.EP182243B02'), ('BMS', 'BMS.EP333541B04'), ('BMS', 'BMS.EP238034B01'), ('BMS', 'BMS.AP298002B02'), ('BMS', 'BMS.EP455759B04'), ('BMS', 'BMS.EP207042B04'), ('BMS', 'BMS.LP128479A01'), ('BMS', 'BMS.LP128476A01'), ('BMS', 'BMS.EP316863B03'), ('BMS', 'BMS.C20'), ('BMS', 'BMS.lp127896a01'), ('BMS', 'BMS.SP491907A02'), ('BMS', 'BMS.EP182060B03'), ('BMS', 'BMS.EP422407B01'), ('BMS', 'BMS.SP573859A04'), ('BMS', 'BMS.SP584547A02'), ('BMS', 'BMS.EP182346B04'), ('BMS', 'BMS.AP668631B04'), ('BMS', 'BMS.EP451428B04'), ('BMS', 'BMS.LP128538A01'), ('BMS', 'BMS.SP490298A02'), ('BMS', 'BMS.SP573860A01'), ('BMS', 'BMS.EP032412B02'), ('BMS', 'BMS.EP163771B01'), ('BMS', 'BMS.LP169879A01'), ('BMS', 'BMS.EP729433A02'), ('BMS', 'BMS.EP447940B04'), ('BMS', 'BMS.SP584551A08'), ('BMS', 'BMS.EP216516B04'), ('BMS', 'BMS.EP023808B02'), ('BMS', 'BMS.BLANK2.2A'), ('BMS', 'BMS.BLANK2.2B'), ('BMS', 'BMS.BLANK2.2C'), ('BMS', 'BMS.BLANK2.2D'), ('BMS', 'BMS.BLANK2.2E'), ('BMS', 'BMS.BLANK2.2F'), ('BMS', 'BMS.BLANK2.2G'), ('BMS', 'BMS.BLANK2.2H'), ('BMS', 'BMS.SP573843A04'), ('BMS', 'BMS.EP683835A01'), ('BMS', 'BMS.SP573824A04'), ('BMS', 'BMS.SP335002A04'), ('BMS', 'BMS.SP478193A02'), ('BMS', 'BMS.SP232311A04'), ('BMS', 'BMS.SP415021A02'), ('BMS', 'BMS.SP231630A02'), ('BMS', 'BMS.SP641029A02'), ('BMS', 'BMS.SP232310A04'), ('BMS', 'BMS.EP617442B01'), ('BMS', 'BMS.EP587478B04'), ('BMS', 'BMS.EP447928B04'), ('BMS', 'BMS.EP587475B04'), ('BMS', 'BMS.EP675042B01'), ('BMS', 'BMS.EP554513B02'), ('BMS', 'BMS.EP702221B04'), ('BMS', 'BMS.AP568787B02'), ('BMS', 'BMS.EP054632B01'), ('BMS', 'BMS.EP121013B01'), ('BMS', 'BMS.EP649418A02'), ('BMS', 'BMS.EP573313B01'), ('BMS', 'BMS.LP154981A01'), ('BMS', 'BMS.AP470859B01'), ('BMS', 'BMS.LP154986A01'), ('BMS', 'BMS.AP732307B04'), ('BMS', 'BMS.EP533426B03'), ('BMS', 'BMS.EP587476B04'), ('BMS', 'BMS.AP696363B02'), ('BMS', 'BMS.EP587477B04'), ('BMS', 'BMS.SP683466A02'), ('BMS', 'BMS.EP554518B04'), ('BMS', 'BMS.EP533429B04'), ('BMS', 'BMS.EP431570B01'), ('BMS', 'BMS.EP202095B04'), ('BMS', 'BMS.EP504030B04'), ('BMS', 'BMS.EP207036B01'), ('BMS', 'BMS.EP393717B01'), ('BMS', 'BMS.SP491898A02'), ('BMS', 'BMS.EP484973B04'), ('BMS', 'BMS.EP479794B02'), ('BMS', 'BMS.EP554515B04'), ('BMS', 'BMS.SP631994A04'), ('BMS', 'BMS.EP921593A04'), ('BMS', 'BMS.AP787247B04'), ('BMS', 'BMS.EP090129B04'), ('BMS', 'BMS.EP447975B02'), ('BMS', 'BMS.EP212214B01'), ('BMS', 'BMS.EP410042B01'), ('BMS', 'BMS.SP404409A02'), ('BMS', 'BMS.SP247340A04'), ('BMS', 'BMS.AP029018B01'), ('BMS', 'BMS.EP872341A01'), ('BMS', 'BMS.AP062219B03'), ('BMS', 'BMS.EP790020A02'), ('BMS', 'BMS.EP808112A04'), ('BMS', 'BMS.SP404403A02'), ('BMS', 'BMS.EP073160B01'), ('BMS', 'BMS.EP012991B03'), ('BMS', 'BMS.SP317297A02'), ('BMS', 'BMS.EP656055A04'), ('BMS', 'BMS.EP649623A01'), ('BMS', 'BMS.EP790019A01'), ('BMS', 'BMS.SP257519A04'), ('BMS', 'BMS.EP808104A01'), ('BMS', 'BMS.EP808106A01'), ('BMS', 'BMS.SP231629A02'), ('BMS', 'BMS.EP675044A01'), ('BMS', 'BMS.EP657260A01'), ('BMS', 'BMS.EP808110A04'), ('BMS', 'BMS.AP032413B04'), ('BMS', 'BMS.EP843906A04'), ('BMS', 'BMS.AP173305B04'), ('BMS', 'BMS.SP231628A02'), ('BMS', 'BMS.AP173301B04'), ('BMS', 'BMS.SP404405A02'), ('BMS', 'BMS.EP649653A04'), ('BMS', 'BMS.EP718687A04'), ('BMS', 'BMS.AP905750A02'), ('BMS', 'BMS.EP738468A01'), ('BMS', 'BMS.C6'), ('BMS', 'BMS.EP890157A02'), ('BMS', 'BMS.SP353893A02'), ('BMS', 'BMS.EP944059A02'), ('BMS', 'BMS.EP970005A01'), ('BMS', 'BMS.EP927461A04'), ('BMS', 'BMS.EP808111A03'), ('BMS', 'BMS.EP927459A04'), ('BMS', 'BMS.SP317293A02'), ('BMS', 'BMS.SP235186A04'), ('BMS', 'BMS.SP399724A04'), ('BMS', 'BMS.EP738469A01'), ('BMS', 'BMS.SP284095A03'), ('BMS', 'BMS.C5'), ('BMS', 'BMS.EP337325B04'), ('BMS', 'BMS.EP759450A04'), ('BMS', 'BMS.BLANK3.3A'), ('BMS', 'BMS.BLANK3.3B'), ('BMS', 'BMS.BLANK3.3C'), ('BMS', 'BMS.BLANK3.3D'), ('BMS', 'BMS.BLANK3.3E'), ('BMS', 'BMS.BLANK3.3F'), ('BMS', 'BMS.BLANK3.3G'), ('BMS', 'BMS.BLANK3.3H'), ('BMS', 'BMS.AP006367B02'), ('BMS', 'BMS.EP929277A02'), ('BMS', 'BMS.AP324642B04'), ('BMS', 'BMS.EP786631A04'), ('BMS', 'BMS.EP657385A04'), ('BMS', 'BMS.SP235189A01'), ('BMS', 'BMS.EP448041B04'), ('BMS', 'BMS.SP231631A02'), ('BMS', 'BMS.SP280481A02'), ('BMS', 'BMS.AP032412B04'), ('BMS', 'BMS.EP649737A03'), ('BMS', 'BMS.AP967057A04'), ('BMS', 'BMS.EP876243A04'), ('BMS', 'BMS.SP229387A04'), ('BMS', 'BMS.EP667743A04'), ('BMS', 'BMS.SP246941A01'), ('BMS', 'BMS.AP745799A04'), ('BMS', 'BMS.SP205732A02'), ('BMS', 'BMS.SP230382A04'), ('BMS', 'BMS.SP230380A02'), ('BMS', 'BMS.SP230381A01'), ('BMS', 'BMS.SP205754A01'), ('BMS', 'BMS.EP606662B04'), ('BMS', 'BMS.AP780167B02'), ('BMS', 'BMS.EP447927B04'), ('BMS', 'BMS.C18'), ('BMS', 'BMS.LP191039A01'), ('BMS', 'BMS.EP606663B04'), ('BMS', 'BMS.EP573296B01'), ('BMS', 'BMS.EP447926B04'), ('BMS', 'BMS.LP127767A01'), ('BMS', 'BMS.EP479266B04'), ('BMS', 'BMS.LP128543A01'), ('BMS', 'BMS.EP479270B03'), ('BMS', 'BMS.EP921594A04'), ('BMS', 'BMS.EP554501B04'), ('BMS', 'BMS.EP542577B04'), ('BMS', 'BMS.EP487995B04'), ('BMS', 'BMS.EP542578B-4'), ('BMS', 'BMS.EP573310B01'), ('BMS', 'BMS.EP244366B01'), ('BMS', 'BMS.EP533389B03'), ('BMS', 'BMS.EP244360B01'), ('BMS', 'BMS.AP911328B01'), ('BMS', 'BMS.AP481403B02'), ('BMS', 'BMS.22.001.801.552.503.00'), ('BMS', 'BMS.EP372981B04'), ('BMS', 'BMS.EP447929B04'), ('BMS', 'BMS.SP573849A04'), ('BMS', 'BMS.SP577399A02'), ('BMS', 'BMS.EP606656B03'), ('BMS', 'BMS.LP166715A01'), ('BMS', 'BMS.AP668628B04'), ('BMS', 'BMS.C14'), ('BMS', 'BMS.EP446610B02'), ('BMS', 'BMS.EP339061B02'), ('BMS', 'BMS.SP681591A04'), ('BMS', 'BMS.EP393712B02'), ('BMS', 'BMS.EP410041B01'), ('BMS', 'BMS.SP453872A01'), ('BMS', 'BMS.22.001.710.503.791.00'), ('BMS', 'BMS.LP128540A01'), ('BMS', 'BMS.EP339053B02'), ('BMS', 'BMS.EP617443B01'), ('BMS', 'BMS.EP190307B01'), ('BMS', 'BMS.AP795068B04'), ('BMS', 'BMS.LP128541A01'), ('BMS', 'BMS.EP584756B04'), ('BMS', 'BMS.SP284096A02'), ('BMS', 'BMS.EP431562B04'), ('BMS', 'BMS.EP685640B01'), ('BMS', 'BMS.EP339059B02'), ('BMS', 'BMS.EP431575B01'), ('BMS', 'BMS.EP379938B01'), ('BMS', 'BMS.EP529635B02'), ('BMS', 'BMS.EP554506B04'), ('BMS', 'BMS.EP455757B04'), ('BMS', 'BMS.SP491900A02'), ('BMS', 'BMS.LP196272A01'), ('BMS', 'BMS.SP704319A04'), ('BMS', 'BMS.EP617441B01'), ('BMS', 'BMS.AP687591B04'), ('BMS', 'BMS.SP640978A02'), ('BMS', 'BMS.EP981129A02'), ('BMS', 'BMS.EP455763B04'), ('BMS', 'BMS.EP339057B02'), ('BMS', 'BMS.SP491897A02'), ('BMS', 'BMS.EP980752B04'), ('BMS', 'BMS.LP128539A01'), ('BMS', 'BMS.EP996831B04'), ('BMS', 'BMS.EP273332B04'), ('BMS', 'BMS.EP483291B04'), ('BMS', 'BMS.EP393715B01'), ('BMS', 'BMS.EP617440B01'), ('BMS', 'BMS.EP729434A01'), ('BMS', 'BMS.SP645141A03'), ('BMS', 'BMS.BLANK4.4A'), ('BMS', 'BMS.BLANK4.4B'), ('BMS', 'BMS.BLANK4.4C'), ('BMS', 'BMS.BLANK4.4D'), ('BMS', 'BMS.BLANK4.4E'), ('BMS', 'BMS.BLANK4.4F'), ('BMS', 'BMS.BLANK4.4G'), ('BMS', 'BMS.BLANK4.4H'), ('BMS', 'BMS.SP232114A04'), ('BMS', 'BMS.EP393714B01'), ('BMS', 'BMS.EP533388B01'), ('BMS', 'BMS.EP724905B01'), ('BMS', 'BMS.EP282108B01'), ('BMS', 'BMS.EP282107B01'), ('BMS', 'BMS.EP001625B01'), ('BMS', 'BMS.EP073209B02'), ('BMS', 'BMS.SP232079A01'), ('BMS', 'BMS.EP772145A02'), ('BMS', 'BMS.AP771472A04'), ('BMS', 'BMS.AP223470B01'), ('BMS', 'BMS.SP404412A02'), ('BMS', 'BMS.EP772143A02'), ('BMS', 'BMS.SP408629A01'), ('BMS', 'BMS.EP749735A07'), ('BMS', 'BMS.EP846485A01'), ('BMS', 'BMS.EP808109A01'), ('BMS', 'BMS.SP416130A04'), ('BMS', 'BMS.EP882752A01'), ('BMS', 'BMS.AP953594A02'), ('BMS', 'BMS.AP046324B02'), ('BMS', 'BMS.AP891020A04'), ('BMS', 'BMS.EP790023A01'), ('BMS', 'BMS.EP657386A01'), ('BMS', 'BMS.EP805337A01'), ('BMS', 'BMS.EP927458A04'), ('BMS', 'BMS.AP173299B04'), ('BMS', 'BMS.EP768164A02'), ('BMS', 'BMS.EP886422A01'), ('BMS', 'BMS.AP103463B01'), ('BMS', 'BMS.AP744361A02'), ('BMS', 'BMS.AP065292B01'), ('BMS', 'BMS.SP257517A04'), ('BMS', 'BMS.EP790021A04'), ('BMS', 'BMS.EP675075A04'), ('BMS', 'BMS.SP388683A02'), ('BMS', 'BMS.SP232309A01'), ('BMS', 'BMS.EP899038A04'), ('BMS', 'BMS.EP636802A-1'), ('BMS', 'BMS.AP046327B02'), ('BMS', 'BMS.EP905975A04'), ('BMS', 'BMS.SP410796A02'), ('BMS', 'BMS.EP784608A01'), ('BMS', 'BMS.EP808105A01'), ('BMS', 'BMS.SP331134A04'), ('BMS', 'BMS.EP718688A01'), ('BMS', 'BMS.SP232270A02'), ('BMS', 'BMS.EP970001A01'), ('BMS', 'BMS.EP001624B01'), ('BMS', 'BMS.EP868682A01'), ('BMS', 'BMS.EP927462A02'), ('BMS', 'BMS.C3'), ('BMS', 'BMS.EP890158A02'), ('BMS', 'BMS.EP023801B04'), ('BMS', 'BMS.EP400447B04'), ('BMS', 'BMS.EP385379B01'), ('BMS', 'BMS.EP385387B01'), ('BMS', 'BMS.EP385384B01'), ('BMS', 'BMS.SP754514A04'), ('BMS', 'BMS.SP415025A01'), ('BMS', 'BMS.SP415023A02'), ('BMS', 'BMS.EP400448B04'), ('BMS', 'BMS.EP479894B04')]})
