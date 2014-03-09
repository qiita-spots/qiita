#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein", "Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

# Adapted from
# https://github.com/leporo/tornado-redis/blob/master/demos/websockets
from json import loads, dumps

from tornadoredis import Client
from tornado.websocket import WebSocketHandler
from tornado.gen import engine, Task
from pyparsing import alphanums, Word, QuotedString, oneOf, Suppress

from ..qiita_core.search import QiitaSearchCriterion, QiitaSearch
from ..qiita_core.exceptions import IncompetentQiitaDeveloperError
from ..qiita_ware.api.analysis_manager import search_analyses
from ..qiita_ware.api.studies_manager import search_studies
from .connections import r_server

#all messages are in json format. They must have the following format:
# "job": jobname
# "msg": message to print
# "analysis": what analysis this is from in format datatype:analysis
# "results": list of files created if any


class MessageHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        self.redis = Client()
        self.redis.connect()

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user is None:
            return ""
        else:
            return user.strip("\" '")

    def on_message(self, msg):
        msginfo = loads(msg)
        #listens for handshake from page
        if "user:" in msginfo["msg"]:
            self.channel = msginfo["msg"].split(":")[1]
            #need to split the rest off to new func so it can be asynchronous
            self.listen()

    # Decorator turns the function into an asynchronous generator object
    @engine
    def listen(self):
        #runs task given, with the yield required to get returned value
        #equivalent of callback/wait pairing from tornado.gen
        yield Task(self.redis.subscribe, self.channel)
        if not self.redis.subscribed:
            self.write_message("ERROR IN SUBSCRIPTION")
        #listen from tornadoredis makes the listen object asynchronous
        #if using standard redis lib, it blocks while listening
        self.redis.listen(self.callback)
        # Try and fight race condition by loading from redis after listen
        # started need to use std redis lib because tornadoredis is in
        # subscribed state
        oldmessages = r_server.lrange(self.channel + ":messages", 0, -1)
        if oldmessages is not None:
            for message in oldmessages:
                self.write_message(message)

    def callback(self, msg):
        if msg.kind == "message":
            self.write_message(str(msg.body))

    @engine
    def on_close(self):
        yield Task(self.redis.unsubscribe, self.channel)
        self.redis.disconnect()


class SearchASHandler(WebSocketHandler):

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if user is None:
            return ""
        else:
            return user.strip("\" '")

    def on_message(self, msg):
        """ Parses sent search and sends back results

        Parameters
        ----------
        msg: json string
            contains "query" key with query string and "type" key with return
            type, e.g. study, analysis, etc.

        Raises
        ------
        IncompetentQiitaDeveloperError
            If type is not recognised
        """
        user = self.get_current_user()
        msginfo = loads(msg)
        query, searchstr = self.ParseSearchString(msginfo["query"])
        if msginfo["type"] == "analysis":
            res = search_analyses(user, query)
        elif msginfo["type"] == "study":
            res = search_studies(user, query)
        else:
            raise IncompetentQiitaDeveloperError("Unrecognised type: %s" %
                                                 msginfo["type"])
        result = []
        for item in res:
            result.append((item.name, item.id))
        result = dumps({
                "results": result,
                "query": searchstr
            })
        self.write_message(result)

    def ParseSearchString(string):
        """ Parses query and returns string of what query ended up as and
        QiitaSearch object of query

        Parameters
        ----------
        string: str
            query string to parse

        Results
        --------
        search: QiitaSearch object
        searchstr: str
            New search string with unparsed sections removed
        """
        search_string = string.lower()
        #define sybols to be used
        word = Word(alphanums)
        quote_word = QuotedString("\"")
        query_type = oneOf("includes startswith endswith < > =")
        field_type = oneOf("metadata author year")
        col = Suppress(":")
        #define chunk of grammar
        query_search = field_type + col + (word + query_type +
                                          (word | quote_word) |
                                          (word | quote_word))
        search = QiitaSearch()
        searchstr = ""
        first = 0
        for match, start, end in query_search.scanString(search_string):
            operator = None
            if first > 0:
                operator = search_string[first:start-1].split(" ")[-1]
                searchstr = " ".join([searchstr, operator])
            if len(match) < 4:
                #pad out to have full information needed
                #add field we are looking at, which equals field_type
                #implicit includes, so add it into the match
                searchstr = " ".join([searchstr, " ".join(match)])
                criterion = QiitaSearchCriterion(match[0], "includes",
                                                 match[1])
            else:
                criterion = QiitaSearchCriterion(match[0], match[1], match[2])
                searchstr = " ".join([searchstr, " ".join(match)])
            search.add_criterion(criterion)
            first = end+1
        return search, searchstr

    def callback(self, msg):
        if msg.kind == "message":
            self.write_message(str(msg.body))
