#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [ "MongoDBConfigFile" ]

import copy
from pynode.resource import *
from pynode.resources import File

class MongoDBConfigFile(Resource):
    _schema = ResourceArgumentSchema([
        # file 
        ("path",        ResourceArgument(required=True, 
                                         expectedType=basestring)), 
        ("action",      ResourceArgumentList(default="create", 
                                             options=[ "create", "delete", "touch" ])), 
        ("backup",      ResourceArgument(expectedType=basestring)), 
        ("mode",        ResourceArgument(expectedType=int)), 
        ("owner",       ResourceArgument(expectedType=basestring)), 
        ("group",       ResourceArgument(expectedType=basestring)), 
        ("content",     ResourceArgument(expectedType=basestring)), 
        
        # basic database configuration
        ("dbpath",              ResourceArgument(expectedType=basestring)), 
        ("port",                ResourceArgument(expectedType=basestring)), 
        ("bind_ip",             ResourceArgument(expectedType=basestring)), 
        ("logpath",             ResourceArgument(expectedType=basestring)), 
        ("logappend",           ResourceArgumentBoolean()), 
        
        # logging
        ("cpu",                 ResourceArgumentBoolean()), 
        ("verbose",             ResourceArgumentBoolean()), 
        
        # security
        ("auth",                ResourceArgumentBoolean()), 
        
        # administration & monitoring
        ("nohttpinterface",     ResourceArgumentBoolean()), 
        ("rest",                ResourceArgumentBoolean()), 
        ("scripting",           ResourceArgumentBoolean()), 
        ("tablescan",           ResourceArgumentBoolean()), 
        ("prealloc",            ResourceArgumentBoolean()), 
        ("nssize",              ResourceArgument(expectedType=int)), 
        ("mms_token",           ResourceArgument(expectedType=basestring)), 
        ("mms_name",            ResourceArgument(expectedType=basestring)), 
        ("mms_interval",        ResourceArgument(expectedType=int)), 
        ("quota",               ResourceArgumentBoolean()), 
        ("quotaFiles",          ResourceArgument(expectedType=int)), 
        
        # replication
        ("autoresync",          ResourceArgumentBoolean()), 
        ("opIdMem",             ResourceArgument(expectedType=int)), 
        ("fastsync",            ResourceArgumentBoolean()), 
        ("oplogSize",           ResourceArgument(expectedType=int)), 
        
        # master-slave replication
        ("master",              ResourceArgumentBoolean()), 
        ("slave",               ResourceArgumentBoolean()), 
        ("source",              ResourceArgument(expectedType=basestring)), 
        ("only",                ResourceArgument(expectedType=basestring)), 
        
        # replica sets
        ("replSet",             ResourceArgument(expectedType=basestring)), 
        ("keyFile",             ResourceArgument(expectedType=basestring)), 
        
        # sharding
        ("shardsvr",            ResourceArgumentBoolean()), 
        
        # journaling
        ("journal",             ResourceArgumentBoolean()), 
        
        # pynode
        ("name",        ResourceArgument(default=lambda r: r.path, 
                                         expectedType=basestring)), 
        ("provider",            ResourceArgument(default="*mongodb.MongoDBConfigFileProvider", 
                                                 expectedType=basestring)), 
    ])

