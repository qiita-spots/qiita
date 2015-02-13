from itertools import chain
from future.utils import viewvalues
from collections import Counter


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
    fullcount = {}
    # zip all samples so that each metadata column found is its own list
    meta_vals = zip(*[samples[sample] for samples in viewvalues(results)
                    for sample in range(len(samples))])
    for pos, cat in enumerate(meta_cols):
        # use Counter object to count all metadata values for a column
        # pos+1 so we skip the sample names list
        fullcount[meta_cols] = Counter(meta_vals[pos + 1])

    # Now get metadata counts for each study, removing sample ids as before
    studycount = {}
    for study_id in results:
        studycount[study_id] = {}
        # zip all samples for a given study so that each metadata column found
        # is its own list
        meta_vals = zip(*[samples[sample] for samples in results[study_id]
                        for sample in range(len(samples))])

        for pos, cat in enumerate(meta_cols):
            # use Counter object to count all metadata values for a column
            # pos+1 so we skip the sample names list
            studycount[study_id][meta_cols] = Counter(meta_vals[pos + 1])

    return fullcount, studycount


def search(searchstr, user):
    """Runs a Study query and returns matching studies and samples

        Parameters
        ----------
        searchstr : str
            Search string to use
        user : User object
            User making the search. Needed for permissions checks.

        Returns
        -------
        dict
            Found samples in format
            {study_id: [[samp_id1, meta1, meta2, ...],
                        [samp_id2, meta1, meta2, ...], ...}
        list
            metadata column names searched for

        Notes
        -----
        Metadata information for each sample is in the same order as the
        metadata columns list returned

        Metadata column names and string searches are case-sensitive
    """
    pass
