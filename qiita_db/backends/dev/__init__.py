#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.0.1-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_db.backends.dev.user_storage import UserStorage as DEVUser
from qiita_db.backends.dev.analysis_storage import AnalysisStorage as DEVAnalysis
from qiita_db.backends.dev.study_storage import StudyStorage as DEVStudy
from qiita_db.backends.dev.sample_storage import SampleStorage as DEVSample
from qiita_db.backends.dev.job_storage import JobStorage as DEVJob
