#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

from pynode.resources import *

version = "libevent-2.0.12-stable"

Package("gcc")
Script(name="libevent", 
       code="""
sudo wget http://monkey.org/~provos/%s.tar.gz && tar -xvf %s.tar.gz && cd %s && ./configure && make && make install
""" % (version, version, version))

