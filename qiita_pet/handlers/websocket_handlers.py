# adapted from
# https://github.com/leporo/tornado-redis/blob/master/demos/websockets
from json import loads, dumps
from itertools import chain

import toredis
from tornado.web import authenticated
from tornado.websocket import WebSocketHandler
from tornado.gen import engine, Task
from future.utils import viewvalues

from moi import r_client
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact
from qiita_core.util import execute_as_transaction


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        # The redis server
        self.r_client = r_client

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
        oldmessages = self.r_client.lrange(self.channel_messages, 0, -1)
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
        self.r_client.delete('%s:messages' % self.channel)
        self.redis.disconnect()


class SelectedSocketHandler(WebSocketHandler, BaseHandler):
    """Websocket for removing samples on default analysis display page"""
    @authenticated
    @execute_as_transaction
    def on_message(self, msg):
        # When the websocket receives a message from the javascript client,
        # parse into JSON
        msginfo = loads(msg)
        default = self.current_user.default_analysis

        if 'remove_sample' in msginfo:
            data = msginfo['remove_sample']
            artifacts = [Artifact(_id) for _id in data['proc_data']]
            default.remove_samples(artifacts, data['samples'])
        elif 'remove_pd' in msginfo:
            data = msginfo['remove_pd']
            default.remove_samples([Artifact(data['proc_data'])])
        elif 'clear' in msginfo:
            data = msginfo['clear']
            artifacts = [Artifact(_id) for _id in data['pids']]
            default.remove_samples(artifacts)
        self.write_message(msg)


class SelectSamplesHandler(WebSocketHandler, BaseHandler):
    """Websocket for selecting and deselecting samples on list studies page"""
    @authenticated
    @execute_as_transaction
    def on_message(self, msg):
        """Selects samples on a message from the user

        Parameters
        ----------
        msg : JSON str
            Message containing sample and prc_data information, in the form
            {proc_data_id': [s1, s2, ...], ...]}
        """
        msginfo = loads(msg)
        default = self.current_user.default_analysis
        default.add_samples(msginfo['sel'])
        # Count total number of unique samples selected and return
        self.write_message(dumps({
            'sel': len(set(
                chain.from_iterable(s for s in viewvalues(msginfo['sel']))))
        }))
