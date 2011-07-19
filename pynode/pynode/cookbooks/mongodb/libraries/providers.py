#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [ "MongoDBConfigFileProvider" ]

import pynode.utils as utils
from pynode.errors import Fail
from pynode.providers import FileProvider

class MongoDBConfigFileProvider(FileProvider):
    def _getContent(self):
        content = self.resource.content
        
        if content is None:
            try:
                from pynode.source import Template as _template
                template = _template("mongodb/mongodb.conf.j2", dict(mongodb=self.resource))
            except:
                utils.log("Template is fucked")
                raise
            return template()
        elif isinstance(content, basestring):
            return content
        elif hasattr(content, "__call__"):
            return content()
        
        raise Fail("Unknown source type for %s: %r" % (self, content))

