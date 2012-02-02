#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2012 Stamped.com"
__license__ = "TODO"

import os, socket
from subprocess import Popen, PIPE
from optparse   import OptionParser
__hostname = socket.gethostname()

def log(s):
    print "%s) %s" % (__hostname, str(s))

def execute(cmd, **kwargs):
    verbose = kwargs.pop('verbose', True)
    
    if verbose:
        log(cmd)
    
    pp     = Popen(cmd, shell=True, stdout=PIPE, **kwargs)
    output = pp.stdout.read().strip()
    status = pp.wait()
    
    return (output, status)

def restart_upstart_daemon(name):
    ret = execute("initctl status %s" % name, verbose=False, stderr=PIPE)
    
    if 0 == ret[1]:
        ret = execute("initctl restart %s" % name)
    elif os.path.exists("/etc/init/%s.conf" % name):
        log("\nWARNING: %s not running; attempting to start\n" % name)
        ret = execute("initctl start %s" % name)
    else:
        return
    
    if 0 == ret[1]:
        log(ret[0])
    else:
        log("\nWARNING: %s failed (%s)\n" % (name, ret[0]))

def sync_repo(path, force=False):
    clean_repo = "git reset --hard HEAD && git clean -fd && "
    cmd = "cd %s && %sgit pull" % (path, clean_repo if force else "")
    execute(cmd)

def parseCommandLine():
    usage    = "Usage: %prog [options]"
    version = "%prog " + __version__
    parser   = OptionParser(usage=usage, version=version)
    
    parser.add_option("-f", "--force", action="store_true", default=False, 
                      help="force cleaning / updating of underlying repositories")
    
    return parser.parse_args()

def main():
    options, args   = parseCommandLine()
    bootstrap       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root            = os.path.dirname(bootstrap)
    stamped         = os.path.join(root, "stamped")
    
    repos = [
        bootstrap, 
        stamped, 
    ]
    
    for repo in repos:
        if os.path.exists(repo):
            sync_repo(repo, options.force)
    
    restart_upstart_daemon("gunicorn_api")
    restart_upstart_daemon("gunicorn_web")
    restart_upstart_daemon("celeryd")

if __name__ == '__main__':
    main()

