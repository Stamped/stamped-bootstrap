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
            pass
    
    if not replSetInitialized:
        utils.log("Waiting for replica set '%s' to come online..." % config._id)
        while True:
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                pprint(status)
                break
            except (AutoReconnect, OperationFailure):
                sleep(1)
                pass
    
    conn.disconnect()
    
    utils.log("Testing connection to replica set '%s'..." % config._id)
    while True:
        try:
            conn = Connection(primary_host, primary_port, slave_okay=True)
            conn.disconnect()
            break
        except (AutoReconnect):
            sleep(2)
            pass
    
    # write replica set configuration now that replica set is online
    conf_str = json.dumps(conf, sort_keys=True, indent=2)
    conf_path = os.path.join(root, "conf/stamped.conf")
    
    utils.write(conf_path, conf_str)
    
    find_wsgi_server = r"ps -e | grep python | grep 'serve\.py' | grep -v grep"
    if 0 == utils.shell2(find_wsgi_server):
        utils.shell2(r"%s | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9" % find_wsgi_server)
    
    """
    utils.log("Running WSGI application server")
    out = open(os.path.join(root, "logs/wsgi.log"), "w")
    app = os.path.join(root, "stamped/sites/stamped.com/bin/serve.py")
    cmd = "nohup bash -c '. %s && %s %s' < /dev/null" % (activate, python, app)
    pp  = Popen(cmd, shell=True, stdout=out, stderr=out)
    
    utils.log("Waiting for WSGI server to come online...")
    while True:
        status = pp.poll()
        if status != None and status != 0:
            # process was terminated, probably abnormally
            utils.log("WSGI server process '%d' terminated with returncode '%d'" % (pp.pid, status))
            sys.exit(1)
        else:
            try:
                utils.getFile("http://0.0.0.0:5000", retry=False)
                break
            except:
                sleep(1)
                pass
    """
    
    utils.log("Initializing cron jobs")
    cron = os.path.join(base, "cron.sh")
    cmd  = "crontab %s" % cron
    pp   = Popen(cmd, shell=True)
    pp.wait()
    
    gunicorn = os.path.join(root, "bin/gunicorn")
    nginx    = os.path.join(root, "bin/nginx")
    
    utils.log("Starting Green Unicorn on port 18000")
    out     = open(os.path.join(root, "logs/gunicorn.log"), "w")
    conf    = "cp /stamped/bootstrap/cookbooks/stamped/files/gunicorn.conf /etc/init/gunicorn.conf"
    strt    = "service gunicorn start"
    cmd     = ". %s && %s && %s" % (activate, conf, strt)
    pp      = Popen(cmd, shell=True, stdout=out, stderr=out)
    
    # path    = os.path.join(root, "stamped/sites/stamped.com/bin/")
    # out     = open(os.path.join(root, "logs/gunicorn.log"), "w")
    # app     = "%s %s -c gunicorn.conf serve:app" % (python, gunicorn)
    # cmd     = "nohup bash -c '. %s && cd %s && %s && cd %s' < /dev/null" % \
    #             (activate, path, app, root)
    # pp      = Popen(cmd, shell=True, stdout=out, stderr=out)
    # # /stamped/bin/python /stamped/bin/gunicorn -c gunicorn.conf serve:app
    
    """
    utils.log("Waiting for Green Unicorn to come online...")
    while True:
        status = pp.poll()
        if status != None and status != 0:
            # process was terminated, probably abnormally
            utils.log("Green Unicorn process '%d' terminated with returncode '%d'" % (pp.pid, status))
            sys.exit(1)
        else:
            try:
                # note: to reenable this, will have to GET a different URL like 0.0.0.0:18000/v0/stamps/show.json
                # and wait for a 401 response to be returned (unauthorized request)
                utils.getFile("http://0.0.0.0:18000", retry=False)
                utils.log("Success!")
                break
            except:
                sleep(1)
                pass
    """
    
    utils.log("Starting nginx on port 5000")
    conf    = os.path.join(root, "stamped/sites/stamped.com/bin/nginx.conf")
    out     = open(os.path.join(root, "logs/nginx.log"), "w")
    app     = "%s -p %s/ -c %s" % (nginx, root, conf)
    cmd     = "nohup bash -c '. %s && %s ' < /dev/null" % (activate, app)
    pp      = Popen(cmd, shell=True, stdout=out, stderr=out)
    # /stamped/bin/nginx -p /stamped/ -c /stamped/stamped/sites/stamped.com/bin/nginx.conf 
    
    """
    utils.log("Waiting for nginx to come online...")
    while True:
        status = pp.poll()
        if status != None and status != 0:
            # process was terminated, probably abnormally
            utils.log("nginx process '%d' terminated with returncode '%d'" % (pp.pid, status))
            sys.exit(1)
        else:
            try:
                # note: to reenable this, will have to GET a different URL like 0.0.0.0:5000/v0/stamps/show.json
                # and wait for a 401 response to be returned (unauthorized request)
                utils.getFile("http://0.0.0.0:5000", retry=False)
                utils.log("Success!")
                break
            except:
                sleep(1)
                pass
    """
    
    """
    utils.log("Populating database with initial data...")
    out = open(os.path.join(root, "logs/initDB.log"), "w")
    app = os.path.join(root, "stamped/sites/stamped.com/bin/api/SampleData.py")
    cmd = "nohup bash -c '. %s && %s %s' < /dev/null" % (activate, python, app)
    
    try:
        pp = Popen(cmd, shell=True, stdout=out, stderr=out)
        pp.wait()
    except Exception as e:
        utils.log("Error populating the database (likely already populated)")
        utils.printException()
    """

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

