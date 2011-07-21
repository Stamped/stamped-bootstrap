#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

try:
    from pymongo import Connection
    from pymongo.errors import *
    from pprint import pprint
    from optparse import OptionParser
    from time import sleep
    import json, os, pickle, sys, utils
except ImportError as e:
    print "warning: cannot initialize instance; bootstrap/init hasn't installed all dependencies"

def replSetInit(config):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    activate = os.path.join(root, "bin/activate")
    
    if len(config.members) <= 1:
        raise Exception("Error: must define at least 2 replica set members")
    
    primary = config.members[0]['host']
    
    if ':' in primary:
        primary_host, primary_port = primary.split(':')
    else:
        primary_host, primary_port = (primary, 27017)
    
    conf = {
        'mongodb' : {
            'host' : primary_host, 
            'port' : int(primary_port), 
        }
    }
    
    print "Initializing replica set '%s' with primary '%s'" % (config._id, primary)
    connecting = True
    while connecting:
        try:
            conn = Connection(primary, slave_okay=True)
            conn.admin.command({'replSetInitiate' : dict(config)})
            connecting = False
        except AutoReconnect:
            sleep(5)
            pass
    
    print "Waiting for replica set '%s' to come online..." % config._id
    initializing = True
    while initializing:
        try:
            status = conn.admin.command({'replSetGetStatus' : 1})
            pprint(status)
            initializing = False
        except (AutoReconnect, OperationFailure):
            sleep(1)
            pass
    
    # write replica set configuration now that replica set is online
    conf_str = pickle.dumps(conf)
    conf_path = os.path.join(root, "conf/stamped.conf")
    
    utils.write(conf_path, conf_str)
    
    populateDB = os.path.join(root, "stamped/sites/stamped.com/bin/api/SampleData.py")
    utils.shell(". %s && python %s" % (activate, populateDB))

def parseCommandLine():
    usage   = "Usage: %prog json-pickled-params"
    version = "%prog " + __version__
    parser  = OptionParser(usage=usage, version=version)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    
    params = utils.AttributeDict(json.loads(args[0].replace("'", '"')))
    return (options, params)

def main():
    # parse commandline
    (options, config) = parseCommandLine()
    
    replSetInit(config)

if __name__ == '__main__':
    main()

