#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os
from subprocess import Popen, PIPE

def execute(cmd, **kwargs):
    verbose = kwargs.pop('verbose', True)
    
    if verbose:
        print cmd
    
    pp     = Popen(cmd, shell=True, stdout=PIPE, **kwargs)
    output = pp.stdout.read().strip()
    status = pp.wait()
    
    return (output, status)

def reload_upstart_daemon(name):
    ret = execute("initctl status %s" % name, verbose=False, stderr=PIPE)
    
    if 0 == ret[1]:
        ret = execute("initctl reload %s" % name)
        print ret[0]
    elif os.path.exists("/etc/init/%s.conf" % name):
        ret = execute("initctl start %s" % name)
        print ret[0]

def main():
    bootstrap = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.dirname(bootstrap)
    stamped = os.path.join(root, "stamped")
    
    repos = [
        bootstrap, 
        stamped
    ]
    
    for repo in repos:
        if os.path.exists(repo):
            cmd = "cd %s && git pull" % repo
            execute(cmd)
    
    reload_upstart_daemon("gunicorn_api")
    reload_upstart_daemon("gunicorn_web")
    reload_upstart_daemon("celeryd")

if __name__ == '__main__':
    main()

