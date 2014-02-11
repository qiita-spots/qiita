#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_db.backends.sql import (SQLUser, SQLAnalysis, SQLStudy, SQLSample,
                                   SQLJob)
from qiita_db.backends.fs import FSUser, FSAnalysis, FSStudy, FSSample, FSJob
from qiita_db.backends.dev import (DEVUser, DEVAnalysis, DEVStudy, DEVSample,
                                   DEVJob)

BACKEND = "SQL"

if BACKEND == "SQL":
    UserStorage = SQLUser
    AnalysisStorage = SQLAnalysis
    StudyStorage = SQLStudy
    SampleStorage = SQLSample
    JobStorage = SQLJob
elif BACKEND == "FS":
    UserStorage = FSUser
    AnalysisStorage = FSAnalysis
    StudyStorage = FSStudy
    SampleStorage = FSSample
    JobStorage = FSJob
elif BACKEND == "DEV":
    UserStorage = DEVUser
    AnalysisStorage = DEVAnalysis
    StudyStorage = DEVStudy
    SampleStorage = DEVSample
    JobStorage = DEVJob
else:
    raise ValueError("Backend not recognized: %s" % BACKEND)
