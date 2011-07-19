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
        content = self.resource.content
        
        if content is None:
            try:
                template = Template(name="mongodb/mongodb.conf.j2", variables=dict(mongodb=self.resource))
            except:
                utils.log("Template is fucked")
                utils.log(dir(Template))
                utils.log(dir(Template.__init__))
                raise
            return template()
        elif isinstance(content, basestring):
            return content
        elif hasattr(content, "__call__"):
            return content()
        
        raise Fail("Unknown source type for %s: %r" % (self, content))

