#adapted from https://github.com/leporo/tornado-redis/blob/master/demos/websockets

from tornadoredis import Client
from app.tasks import r_server
from tornado.websocket import WebSocketHandler
import tornado.gen
from json import loads

#all messages are in json format. They must have the following format:
# 'job': jobname
# 'msg': message to print
# 'analysis': what analysis this is from in format datatype:analysis
# 'results': list of files created if any


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        self.redis = Client()
        self.redis.connect()

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user == None:
            return ''
        else:
            return user.strip('" ')

    def on_message(self, msg):
        msginfo = loads(msg)
        #listens for handshake from page
        if "user:" in msginfo['msg']:
            self.channel = msginfo['msg'].split(':')[1]
            #need to split the rest off to new func so it can be asynchronous
            self.listen()


    #decorator turns the function into an asynchronous generator object
    @tornado.gen.engine
    def listen(self):
        #runs task given, with the yield required to get returned value
        #equivalent of callback/wait pairing from tornado.gen
        yield tornado.gen.Task(self.redis.subscribe, self.channel)
        if not self.redis.subscribed:
            self.write_message('ERROR IN SUBSCRIPTION')
        #listen from tornadoredis makes the listen object asynchronous
        #if using standard redis lib, it blocks while listening
        self.redis.listen(self.callback)
        #try and fight race condition by loading from redis after listen started
        #need to use std redis lib because tornadoredis is in subscribed state
        oldmessages = r_server.lrange(self.channel + ':messages', 0, -1)
        if oldmessages != None:
            for message in oldmessages:
                self.write_message(message)

    def callback(self, msg):
        if msg.kind == 'message':
            self.write_message(str(msg.body))

    @tornado.gen.engine
    def on_close(self):
        yield tornado.gen.Task(self.redis.unsubscribe, self.channel)
        self.redis.disconnect()