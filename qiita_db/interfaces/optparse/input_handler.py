__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiita_db.backends.sql.parse import parse_mapping_file_to_dicts
from qiita_db.backends.sql.exceptions import QiitaDBSQLParseError
from re import search


def load_mapping_file(mapping_fp):
    """Loads the mapping file information stored in the file mapping_fp

    Returns:
        study_id: study id, extracted from the filepath
        mapping: a dict of dicts representing the mapping file. Outer keys are
            sample names and inner keys are column headers.
        headers: a list of column headers
        datatypes: the datatypes of the columns, automatically determined to be
            varchar, int, or float
    """
    # Parse the mapping file contents
    with open(mapping_fp, 'U') as map_lines:
        mapping, headers, datatypes = parse_mapping_file_to_dicts(map_lines)

    # Parse the study id from the filepath
    study_id = search('study_(\d+)_mapping_file.txt', mapping_fp)
    if study_id:
        study_id = study_id.group(1)
    else:
        raise QiitaDBSQLParseError("Could not parse study id from filename: %s"
                                   % mapping_fp)

    return (study_id, mapping, headers, datatypes)
