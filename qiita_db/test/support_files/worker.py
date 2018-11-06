#!/usr/bin/env python
from json import dumps

# we should test:
# print (dumps({'archive': '/path/to/archive', 'biom': None}))
# print (dumps({'archive': '/path/to/archive', 'biom': 'None'}))
# print (dumps({'archive': None, 'biom': '/path/to/biom'}))
# print (dumps({'archive': 'None', 'biom': '/path/to/biom'}))
print (dumps({'archive': '/path/to/archive', 'biom': '/path/to/biom'}))
