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


def transform_date(value):
    # for the way the patches are applied we need to have this import and
    # the next 2 variables within this function
    from datetime import datetime

    # old format : new format
    formats = {
        # 4 digits year
        '%m/%d/%Y %H:%M:%S': '%Y-%m-%d %H:%M:%S',
        '%m-%d-%Y %H:%M': '%Y-%m-%d %H:%M',
        '%m/%d/%Y %H': '%Y-%m-%d %H',
        '%m-%d-%Y': '%Y-%m-%d',
        '%m-%Y': '%Y-%m',
        '%Y': '%Y',
        # 2 digits year
        '%m/%d/%y %H:%M:%S': '%Y-%m-%d %H:%M:%S',
        '%m-%d-%y %H:%M': '%Y-%m-%d %H:%M',
        '%m/%d/%y %H': '%Y-%m-%d %H',
        '%m-%d-%y': '%Y-%m-%d',
        '%m-%y': '%Y-%m',
        '%y': '%Y'
    }

    # loop over the old formats to see which one is it
    if value is not None:
        date = None
        for i, fmt in enumerate(formats):
            try:
                date = datetime.strptime(value, fmt)
                break
            except ValueError:
                pass
        if date is not None:
            value = date.strftime(formats[fmt])

    return value


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
            # getting just the columns of interest
            st_df = st.to_dataframe()[columns]
            # converting to datetime
            for col in columns:
                st_df[col] = st_df[col].apply(transform_date)
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
            # getting just the columns of interest
            pt_df = pt.to_dataframe()[columns]
            # converting to datetime
            for col in columns:
                pt_df[col] = pt_df[col].apply(transform_date)
            pt.update(pt_df)
