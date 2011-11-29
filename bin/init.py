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
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(base))
    
    activate = os.path.join(root, "bin/activate")
    python   = os.path.join(root, "bin/python")
    
    role = config.role
    config.pop('role')

    if len(config.members) <= 1:
        raise Exception("Error: must define at least 2 replica set members")
    
    primary = config.members[0]['host']
    
    if ':' in primary:
        primary_host, primary_port = primary.split(':')
        primary_port = int(primary_port)
    else:
        primary_host, primary_port = (primary, 27017)
    
    conf = {
        'mongodb' : {
            'host' : primary_host, 
            'port' : int(primary_port), 
        }
    }
    
    utils.log("Initializing replica set '%s' with primary '%s'" % (config._id, primary))
    replSetInitialized = False
    
    while True:
        try:
            conn = Connection(primary_host, primary_port, slave_okay=True)
            
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                utils.log("Replica set '%s' already online" % config._id)
                replSetInitialized = True
                break
            except:
                pass
            
            conn.admin.command({'replSetInitiate' : dict(config)})
            break
        except AutoReconnect:
            sleep(5)
    
    if not replSetInitialized:
        utils.log("Waiting for replica set '%s' to come online..." % config._id)
        while True:
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                pprint(status)
                break
            except (AutoReconnect, OperationFailure):
                sleep(1)
    
    conn.disconnect()
    
    utils.log("Testing connection to replica set '%s'..." % config._id)
    while True:
        try:
            conn = Connection(primary_host, primary_port, slave_okay=True)
            conn.disconnect()
            break
        except (AutoReconnect):
            sleep(2)
    
    # write replica set configuration now that replica set is online
    """
    conf_str = json.dumps(conf, sort_keys=True, indent=2)
    conf_path = os.path.join(root, "conf/stamped.conf")
    
    utils.write(conf_path, conf_str)
    
    find_wsgi_server = r"ps -e | grep python | grep 'serve\.py' | grep -v grep"
    if 0 == utils.shell2(find_wsgi_server):
        utils.shell2(r"%s | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9" % find_wsgi_server)
    """
    
    utils.log("Initializing cron jobs")
    cron = os.path.join(base, "cron.api.sh")
    cmd  = "crontab %s" % cron
    pp   = Popen(cmd, shell=True)
    pp.wait()
    
    gunicorn = os.path.join(root, "bin/gunicorn")
    nginx    = os.path.join(root, "bin/nginx")

    if role == 'api':
        utils.log("Starting Green Unicorn on port 18000")
        out     = open(os.path.join(root, "logs/gunicorn_api.log"), "w")
        strt    = "/stamped/bin/python /stamped/bin/gunicorn_django -c /stamped/stamped/sites/stamped.com/bin/httpapi/gunicorn.conf /stamped/stamped/sites/stamped.com/bin/httpapi/settings.py"
        cmd     = ". %s && %s" % (activate, strt)
        pp      = Popen(cmd, shell=True, stdout=out, stderr=out)

        utils.log("Starting nginx on port 5000")
        conf    = os.path.join(root, "stamped/sites/stamped.com/bin/httpapi/nginx.conf")
        out     = open(os.path.join(root, "logs/nginx_api.log"), "w")
        app     = "%s -p %s/ -c %s" % (nginx, root, conf)
        cmd     = "nohup bash -c '. %s && %s ' < /dev/null" % (activate, app)
        pp      = Popen(cmd, shell=True, stdout=out, stderr=out)

    elif role == 'web':
    
        utils.log("Starting Green Unicorn on port 19000")
        out     = open(os.path.join(root, "logs/gunicorn_web.log"), "w")
        strt    = "/stamped/bin/python /stamped/bin/gunicorn_django -c /stamped/stamped/sites/stamped.com/bin/www/gunicorn.conf /stamped/stamped/sites/stamped.com/bin/www/settings.py"
        cmd     = ". %s && %s" % (activate, strt)
        pp      = Popen(cmd, shell=True, stdout=out, stderr=out)

        utils.log("Starting nginx on port 5000")
        conf    = os.path.join(root, "stamped/sites/stamped.com/bin/www/nginx.conf")
        out     = open(os.path.join(root, "logs/nginx_web.log"), "w")
        app     = "%s -p %s/ -c %s" % (nginx, root, conf)
        cmd     = "nohup bash -c '. %s && %s ' < /dev/null" % (activate, app)
        pp      = Popen(cmd, shell=True, stdout=out, stderr=out)

    else:
        utils.log("Not an 'api' or 'web' instance!")        


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

