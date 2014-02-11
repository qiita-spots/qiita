#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_db.backends.sql.user_storage import UserStorage as SQLUser
from qiita_db.backends.sql.analysis_storage import AnalysisStorage as SQLAnalysis
from qiita_db.backends.sql.study_storage import StudyStorage as SQLStudy
from qiita_db.backends.sql.sample_storage import SampleStorage as SQLSample
from qiita_db.backends.sql.job_storage import JobStorage as SQLJob
