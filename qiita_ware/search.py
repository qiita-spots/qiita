from collections import Counter

from future.utils import viewvalues

from qiita_db.search import QiitaStudySearch


def count_metadata(results, meta_cols):
    """Counts the metadata found in a search, and returns these counts

    Parameters
    ----------
    results : dict of lists of list
        results in the format returned by the qiita_db search obj
    meta_cols : list
        metadata column names searched for, as returned by qiita_db search obj

    Returns
    -------
    fullcount : dict of dicts
        counts for each found metadata value over all studies, in the format
        {meta_col1: {value1: count, value2: count, ...}, ...}
    studycount : dict of dict of dicts
        counts for each found metadata value for each study, in the format
        {study_id: {meta_col1: {value1: count, value2: count, ...}, ...}, ...}
    """
    def double_comprehension(results):
        for samples in viewvalues(results):
            for sample in samples:
                yield sample

    fullcount = {}
    # rearrange all samples so that each metadata column found is its own list
    meta_vals = zip(*double_comprehension(results))
    for pos, cat in enumerate(meta_cols):
        # use Counter object to count all metadata values for a column
        # pos+1 so we skip the sample names list
        fullcount[cat] = Counter(meta_vals[pos + 1])

    # Now get metadata counts for each study, removing sample ids as before
    studycount = {}
    for study_id in results:
        studycount[study_id] = {}
        # zip all samples for a given study so that each metadata column found
        # is its own list
        meta_vals = zip(*(sample for sample in results[study_id]))
        for pos, cat in enumerate(meta_cols):
            # use Counter object to count all metadata values for a column
            # pos+1 so we skip the sample names list
            studycount[study_id][cat] = Counter(meta_vals[pos + 1])

    return fullcount, studycount


def search(searchstr, user, study=None):
    """ Passthrough for qiita_db search object. See object for documentation
    """
    search = QiitaStudySearch()
    return search(searchstr, user, study)
