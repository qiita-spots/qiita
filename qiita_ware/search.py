from collections import Counter, defaultdict

from future.utils import viewvalues

from qiita_db.study import Study
from qiita_db.data import ProcessedData
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


def filter_by_processed_data(results, datatypes=None):
    """Filters results to what is available in each processed data

    Parameters
    ----------
    results : dict of lists of list
        results in the format returned by the qiita_db search obj
    datatypes : list of str, optional
        Datatypes to selectively return. Default all datatypes available

    Returns
    -------
    study_proc_ids : dict of dicts of lists
        Processed data ids with samples for each study, in the format
        {study_id: {datatype: [proc_id, proc_id, ...], ...}, ...}
    proc_data_samples : dict of lists of lists
        Samples available in each processed data id, in the format
        {proc_data_id: [[samp_id1, meta1, meta2, ...],
                        [samp_id2, meta1, meta2, ...], ...}
    dtcount : count of all samples available for each datatype
    """
    study_proc_ids = {}
    proc_data_samples = {}
    dtcount = defaultdict(int)
    for study_id in results:
        study = Study(study_id)
        study_proc_ids[study_id] = defaultdict(list)
        for proc_data_id in study.processed_data():
            proc_data = ProcessedData(proc_data_id)
            datatype = proc_data.data_type()
            # skip processed data if it doesn't fit the given datatypes
            if datatypes is not None and datatype not in datatypes:
                continue
            samps_available = set(proc_data.samples)
            proc_data_samples[proc_data_id] = [s for s in results[study_id]
                                               if s[0] in samps_available]
            # Add number of samples left to the total for that datatype
            pidlen = len(proc_data_samples[proc_data_id])
            dtcount[datatype] += pidlen
            if pidlen == 0:
                # all samples filtered so remove it as a result
                del(proc_data_samples[proc_data_id])
            else:
                # add the processed data to the list for the study
                study_proc_ids[study_id][datatype].append(proc_data_id)
    return study_proc_ids, proc_data_samples, dtcount


def search(searchstr, user, remove_selected=False, analysis=None):
    """ Passthrough for qiita_db search object. See object for documentation
    """
    search = QiitaStudySearch()
    return search(searchstr, user, remove_selected, analysis)
