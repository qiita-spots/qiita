#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The QiiTa Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.0.1-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita.qiita_db.backends.fs.user_storage.py import UserStorage as FSUser
from qiita.qiita_db.backends.fs.analysis_storage.py import AnalysisStorage as FSAnalysis
from qiita.qiita_db.backends.fs.study_storage.py import StudyStorage as FSStudy
from qiita.qiita_db.backends.fs.sample_storage.py import SampleStorage as FSSample
from qiita.qiita_db.backends.fs.job_storage.py import JobStorage as FSJob