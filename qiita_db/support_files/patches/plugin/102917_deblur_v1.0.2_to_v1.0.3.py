# script first deployed in the qiita machine on 10/27/17 and
# redeployed on 10/31/17 so all artifacts were fixed

from sys import argv
from qiita_db.artifact import Artifact
from biom import load_table
from qiita_db.util import compute_checksum
from qiita_db.sql_connection import TRN
from biom.util import biom_open
from skbio.io import read
from os import rename, remove


if len(argv) == 1:
    raise ValueError('You need to pass some arguments')

artifacts = [Artifact(aid) for aid in argv[1:]]

sql = "UPDATE qiita.filepath SET checksum = %s WHERE filepath_id = %s"
for a in artifacts:
    for _id, fp, fpt in a.filepaths:
        # putting all this in a transaction in case something fails it does
        # it nicely
        with TRN:
            checksum = None
            if fpt == 'biom':
                t = load_table(fp)
                current = t.ids('observation')
                updated = map(lambda x: x.upper(), current)
                if len(set(updated)) != len(updated):
                    print '************>', a.id, fp, '<**************'
                if set(current) ^ set(updated):
                    print 'Changing biom: ', a.id, fp
                    t.update_ids({i: i.upper() for i in t.ids('observation')},
                                 axis='observation', inplace=True)
                    with biom_open(fp, 'w') as f:
                        t.to_hdf5(f, t.generated_by)
                    checksum = compute_checksum(fp)
            elif fpt == 'preprocessed_fasta':
                changed = False
                tmp = fp + '.tmp'
                with open(tmp, 'w') as out:
                    for seq in read(fp, format='fasta'):
                        seq = str(seq)
                        sequ = seq.upper()
                        out.write('>%s\n%s\n' % (sequ, sequ))
                        if seq != sequ:
                            changed = True
                if changed:
                    print 'Changing biom: ', a.id, fp
                    rename(tmp, fp)
                    checksum = compute_checksum(fp)
                else:
                    remove(tmp)

            if checksum is not None:
                TRN.add(sql, [checksum, _id])
                TRN.execute()
