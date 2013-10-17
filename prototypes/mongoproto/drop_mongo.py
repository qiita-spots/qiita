#!/usr/bin/env python

import pymongo

client = pymongo.MongoClient('localhost', 27017)
db = client.prototype
db.metadata.remove()
