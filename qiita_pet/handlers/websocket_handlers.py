# adapted from
# https://github.com/leporo/tornado-redis/blob/master/demos/websockets
from time import sleep

from tornado.websocket import WebSocketHandler
from tornado.gen import engine, Task
from json import loads

# all messages are in json format. They must have the following format:
# 'analysis': analysis_id
# 'msg': message to print
# 'command': what command this is from in format datatype#command


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        # self.redis = Client()
        # self.redis.connect()

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user is None:
            return ''
        else:
            return user.strip('" ')

    def on_message(self, msg):
        msginfo = loads(msg)
        # listens for handshake from page
        if "user:" in msginfo['msg']:
            self.aid = msginfo['msg'].split()[0]
            self.channel = msginfo['msg'].split()[1].split(':')[1]
            # need to split the rest off to new func so it can be asynchronous
            self.listen()

    # decorator turns the function into an asynchronous generator object
    @engine
    def listen(self):
        sleep(5)
        self.write_message({"analysis": self.aid, "msg": "allcomplete"})

    def callback(self, msg):
        if msg.kind == 'message':
            self.write_message(str(msg.body))

    @engine
    def on_close(self):
        yield Task(self.redis.unsubscribe, self.channel)
        self.redis.disconnect()