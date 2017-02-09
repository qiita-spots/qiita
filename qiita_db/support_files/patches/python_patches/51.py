from future.utils import viewitems
from datetime import datetime

from qiita_db.metadata_template.constants import (
    SAMPLE_TEMPLATE_COLUMNS, PREP_TEMPLATE_COLUMNS,
    PREP_TEMPLATE_COLUMNS_TARGET_GENE)
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.sql_connection import TRN

# getting columns in each info file that we need to check for
cols_sample = [col
               for key, vals in viewitems(SAMPLE_TEMPLATE_COLUMNS)
               for col, dt in viewitems(vals.columns) if dt == datetime]
cols_prep = [col
             for key, vals in viewitems(PREP_TEMPLATE_COLUMNS)
             for col, dt in viewitems(vals.columns) if dt == datetime].extend(
                [col
                 for key, vals in viewitems(PREP_TEMPLATE_COLUMNS_TARGET_GENE)
                 for col, dt in viewitems(vals.columns)])

if cols_sample:
    with TRN:
        # a few notes: just getting the preps with duplicated values; ignoring
        # column 'sample_id' and tables 'study_sample', 'prep_template',
        # 'prep_template_sample'
        sql = """SELECT table_name, array_agg(column_name::text)
                    FROM information_schema.columns
                    WHERE column_name IN %s
                        AND table_name LIKE 'sample_%%'
                        AND table_name NOT IN (
                            'prep_template', 'prep_template_sample')
                    GROUP BY table_name"""
        # note that we are looking for those columns with duplicated names in
        # the headers
        TRN.add(sql, [tuple(set(cols_sample))])
        for table, columns in viewitems(dict(TRN.execute_fetchindex())):
            # [1] the format is table_# so taking the #
            st = SampleTemplate(int(table.split('_')[1]))
            st_df = st.to_dataframe()[columns]
            st_df.replace({'/': '-'}, regex=True, inplace=True)
            st.update(st_df)

if cols_prep:
    with TRN:
        # a few notes: just getting the preps with duplicated values; ignoring
        # column 'sample_id' and tables 'study_sample', 'prep_template',
        # 'prep_template_sample'
        sql = """SELECT table_name, array_agg(column_name::text)
                    FROM information_schema.columns
                    WHERE column_name IN %s
                        AND table_name LIKE 'prep_%%'
                        AND table_name NOT IN (
                            'prep_template', 'prep_template_sample')
                    GROUP BY table_name"""
        # note that we are looking for those columns with duplicated names in
        # the headers
        TRN.add(sql, [tuple(set(cols_prep))])
        for table, columns in viewitems(dict(TRN.execute_fetchindex())):
            # [1] the format is table_# so taking the #
            pt = PrepTemplate(int(table.split('_')[1]))
            pt_df = pt.to_dataframe()[columns]
            pt_df.replace({'/': '-'}, regex=True, inplace=True)
            pt.update(pt_df)
