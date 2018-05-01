# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.study import Study

studies = Study.get_by_status('private').union(
    Study.get_by_status('public')).union(Study.get_by_status('sandbox'))
raw_data = [pt.artifact for s in studies for pt in s.prep_templates()
            if pt.artifact is not None]

for rd in raw_data:
    # getting the most open visibility of all the children in the pipeline
    children = rd.descendants.nodes()
    vis = [a.visibility for a in children]
    vis.append(rd.visibility)

    new_vis = 'sandbox'
    if 'public' in vis:
        new_vis = 'public'
    elif 'private' in vis:
        new_vis = 'private'

    rd.visibility = new_vis
