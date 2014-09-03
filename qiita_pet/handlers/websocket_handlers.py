# adapted from
# https://github.com/leporo/tornado-redis/blob/master/demos/websockets
from json import loads

from qiita_ware.run import r_server

from toredis import Client
from tornado.websocket import WebSocketHandler
from tornado.gen import engine, Task

# all messages are in json format. They must have the following format:
# 'analysis': analysis_id
# 'msg': message to print
# 'command': what command this is from in format datatype#command


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        self.redis = Client()
        self.redis.connect()

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user is None:
            return ''
        else:
            return user.strip('" ')

    def on_message(self, msg):
        msginfo = loads(msg)
        # listens for handshake from page
        self.channel = msginfo['user']
        # need to split the rest off to new func so it can be asynchronous
        self.listen()

    def listen(self):
        # runs task given, with the yield required to get returned value
        # equivalent of callback/wait pairing from tornado.gen
        self.redis.subscribe(self.channel, callback=self.callback)
        # fight race condition by loading from redis after listen started
        oldmessages = r_server.lrange('%s:messages' % self.channel, 0, -1)
        if oldmessages is not None:
            for message in oldmessages:
                self.write_message(message)

    def callback(self, msg):
        print ">>>>>>>>>>>>>>", msg
        if msg[0] == 'message':
            self.write_message(msg[2])

    @engine
    def on_close(self):
        yield Task(self.redis.unsubscribe, self.channel)
        self.redis.disconnect()
