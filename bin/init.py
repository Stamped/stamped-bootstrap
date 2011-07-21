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
    from subprocess import Popen, PIPE
    import json, os, pickle, sys, urllib2, utils
except ImportError:
     print "error: cannot initialize instance; bootstrap/init hasn't installed all dependencies"
     raise

def replSetInit(config):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    activate = os.path.join(root, "bin/activate")
    python   = os.path.join(root, "bin/python")
    
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
    
    utils.log("Initializing replica set '%s' with primary '%s'" % (config._id, primary))
    connecting = True
    initializing = True
    
    while connecting:
        try:
            conn = Connection(primary, slave_okay=True)
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                utils.log("Replica set '%s' already online" % config._id)
                connecting   = False
                initializing = False
                break
            except:
                pass
            
            conn.admin.command({'replSetInitiate' : dict(config)})
            connecting = False
        except AutoReconnect:
            sleep(5)
            pass
    
    if initializing:
        utils.log("Waiting for replica set '%s' to come online..." % config._id)
        while initializing:
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                pprint(status)
                initializing = False
            except (AutoReconnect, OperationFailure):
                sleep(1)
                pass
    
    # write replica set configuration now that replica set is online
    conf_str = json.dumps(conf, sort_keys=True, indent=2)
    conf_path = os.path.join(root, "conf/stamped.conf")
    
    utils.write(conf_path, conf_str)
    
    utils.log("Running WSGI application server")
    out = open(os.path.join(root, "logs/wsgi.log"), "w")
    app = os.path.join(root, "stamped/sites/stamped.com/bin/serve.py")
    cmd = ". %s && %s %s" % (activate, python, app)
    pp  = Popen(cmd, shell=True, stdout=out, stderr=out)
    
    utils.log("Waiting for WSGI server to come online...")
    while True:
        status = pp.poll()
        if status != None:
            # process was terminated, probably abnormally
            utils.log("WSGI server process '%d' terminated with returncode '%d'" % (pp.pid, status))
            sys.exit(1)
        else:
            try:
                utils.getFile("0.0.0.0:5000")
                break
            except:
                sleep(1)
                pass
    
    utils.log("Populating database with initial data...")
    app = os.path.join(root, "stamped/sites/stamped.com/bin/api/SampleData.py")
    cmd = ". %s && %s %s" % (activate, python, app)
    pp  = Popen(cmd, shell=True).wait()

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

