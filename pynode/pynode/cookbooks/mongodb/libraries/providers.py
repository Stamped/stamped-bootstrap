#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [ "MongoDBConfigFileProvider" ]

import pynode.utils as utils
from pynode.errors import Fail
from pynode.providers import *
from pynode.source import Template

class MongoDBConfigFileProvider(FileProvider):
    def _getContent(self):
        print "MongoDBConfigFileProvider"
        content = self.resource.content
        print content
        
        if content is None:
            return None
        elif isinstance(content, basestring):
            return content
        elif isinstance(content, dict):
            template = Template("mongodb/mongodb.conf.j2", variables=dict(mongodb=content))
            return template()
        elif hasattr(content, "__call__"):
            return content()
        
        raise Fail("Unknown source type for %s: %r" % (self, content))

