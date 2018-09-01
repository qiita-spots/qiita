# August 31, 2018
# Strip any UTF-8 characters that are not also printable ASCII characters
# from study titles. As some analysis packages cannot interpret UTF-8
# characters, it becomes important to remove them from study titles, as
# they are used as metadata/identifiers when creating new analyses.
from json import dumps
from qiita_db.study import Study
from re import sub

studies = Study.get_by_status('public')

for study in studies:
    title = study.title
    print(title)
    #new_title = sub(r'[^\x20-\x7E]+', '', title)
    #print(new_title)
    #study.title = new_title
    #study.set('title', re.sub(r'[^\x20-\x7E]+', '', title))

