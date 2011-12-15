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
    
    return Popen(cmd, shell=True, **kwargs).wait()

def reload_upstart_daemon(name):
    ret = execute("initctl status %s" % name, verbose=False, stdout=PIPE, stderr=PIPE)
    
    if 0 == ret:
        execute("initctl reload %s" % name)
    elif os.path.exists("/etc/init/%s.conf"):
        execute("initctl start %s" % name)

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
    
    reload_upstart_daemon("reload gunicorn_api")
    reload_upstart_daemon("reload gunicorn_web")
    reload_upstart_daemon("reload celeryd")

if __name__ == '__main__':
    main()

