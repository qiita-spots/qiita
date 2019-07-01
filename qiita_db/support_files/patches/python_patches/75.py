from qiita_db.user import User
from qiita_core.qiita_settings import r_client


# one of the main side issues raised by #2901 is that new users emails were not
# added to the redis database that keep track of emails and is used to
# autocomplete when sharing a study. In the next look we will find all `Users`
# in the `user` level, search them in the redis database, and keep those ones
# that are not found
missing_emails = [u[0] for u in User.iter() if User(u[0]).level == 'user'
                  and not r_client.execute_command(
                      'zrangebylex', 'qiita-usernames',
                      '[%s' % u[0], u'[%s\xff' % u[0])]

# now just add them
for email in missing_emails:
    r_client.zadd('qiita-usernames', {email: 0})
