from qiita_db.user import User
from qiita_core.qiita_settings import r_client

missing_emails = [u[0] for u in User.iter() if User(u[0]).level == 'user'
                  and not r_client.execute_command(
                      'zrangebylex', 'qiita-usernames',
                      '[%s' % u[0], u'[%s\xff' % u[0])]

for email in missing_emails:
    r_client.zadd('qiita-usernames', {email: 0})
