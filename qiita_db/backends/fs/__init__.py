#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.0.1-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_db.backends.fs.user_storage import UserStorage as FSUser
from qiita_db.backends.fs.analysis_storage import AnalysisStorage as FSAnalysis
from qiita_db.backends.fs.study_storage import StudyStorage as FSStudy
from qiita_db.backends.fs.sample_storage import SampleStorage as FSSample
from qiita_db.backends.fs.job_storage import JobStorage as FSJob