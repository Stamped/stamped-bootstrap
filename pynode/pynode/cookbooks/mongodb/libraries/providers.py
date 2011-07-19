#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [ "MongoDBConfigFileProvider" ]

import pynode.utils as utils
from pynode.errors import Fail
from pynode.provider import Provider

class MongoDBConfigFileProvider(Provider):
    def action_create(self):
        virtualenv.create_environment(home_dir=self.resource.path, 
                                      site_packages=self.resource.site_packages, 
                                      clear=self.resource.clear, 
                                      unzip_setuptools=self.resource.unzip_setuptools, 
                                      use_distribute=self.resource.use_distribute, 
                                      never_download=self.resource.never_download)
        
        log("Installed virtualenv '%s'" % self.resource.path)
    
    def action_delete(self):
        (output, status) = shell('rm -rf %s' % self.resource.path)
        if 0 != status:
            raise Fail("unable to delete virtualenv %s" % self.resource.name)

