# adapted from
# https://github.com/leporo/tornado-redis/blob/master/demos/websockets
from json import loads

import toredis
from tornado.web import authenticated
from tornado.websocket import WebSocketHandler
from tornado.gen import engine, Task

from qiita_ware import r_server


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        # The redis server
        self.r_server = r_server

        # The toredis server that allows event-based message handling
        self.toredis = toredis.Client()
        self.toredis.connect()

        self.channel = None
        self.channel_messages = None

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user is None:
            raise ValueError("No user associated with the websocket!")
        else:
            return user.strip('" ')

    @authenticated
    def on_message(self, msg):
        # When the websocket receives a message from the javascript client,
        # parse into JSON
        msginfo = loads(msg)

        # Determine which Redis communication channel the server needs to
        # listen on
        self.channel = msginfo.get('user', None)

        if self.channel is not None:
            self.channel_messages = '%s:messages' % self.channel
            self.listen()

    def listen(self):
        # Attach a callback on the channel to listen too. This callback is
        # executed when anything is placed onto the channel.
        self.toredis.subscribe(self.channel, callback=self.callback)

        # Potential race-condition where a separate process may have placed
        # messages into the queue before we've been able to attach listen.
        oldmessages = self.r_server.lrange(self.channel_messages, 0, -1)
        if oldmessages is not None:
            for message in oldmessages:
                self.write_message(message)

    def callback(self, msg):
        message_type, channel, payload = msg

        # if a compute process wrote to the Redis channel that we are
        # listening too, and if it is actually a message, send the payload to
        # the javascript client via the websocket
        if channel == self.channel and message_type == 'message':
            self.write_message(payload)

    @engine
    def on_close(self):
        yield Task(self.toredis.unsubscribe, self.channel)
        self.r_server.delete('%s:messages' % self.channel)
        self.redis.disconnect()
