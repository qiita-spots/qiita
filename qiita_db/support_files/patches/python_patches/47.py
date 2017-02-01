from qiita_db.study import Study


class ForRecursion(object):
    """for some strange reason, my guess is how we are executing the patches
    recursion doesn't work directly so decided to use a class to make it
    work"""

    @classmethod
    def change_status(cls, artifact, status):
        for a in artifact.children:
            try:
                a.visibility = status
            except:
                # print so we know which changes failed and we can deal by hand
                print "failed aid: %d, status %s" % (artifact.id, status)
                return
            cls.change_status(a, status)


studies = Study.get_by_status('private').union(
    Study.get_by_status('public')).union(Study.get_by_status('sandbox'))
# just getting the base artifacts, no parents
artifacts = {a for s in studies for a in s.artifacts() if not a.parents}

# inheriting status
fr = ForRecursion
for a in artifacts:
    status = a.visibility
    fr.change_status(a, status)
