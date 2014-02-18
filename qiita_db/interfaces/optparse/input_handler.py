__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from re import search
from qiita_db.backends.sql.exceptions import QiitaDBSQLParseError
from qiita_core.metadata_map import MetadataMap


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
        metadata_map = MetadataMap.parseMetadataMap(map_lines)

    print MetadataMap
    print metadata_map.__class__

    # TO BE REFACTORED: this entire piece of code should be refactored
    # once we have clear how we are going to get the maetadata map ID
    # which consist of a tuple (study id, metadata map num).
    # Parse the study id from the filepath
    study_id = search('study_(\d+)_mapping_file.txt', mapping_fp)
    if study_id:
        study_id = study_id.group(1)
    else:
        raise QiitaDBSQLParseError("Could not parse study id from filename: %s"
                                   % mapping_fp)
    metadata_map.set_id(study_id, 0)

    return metadata_map
