#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2012 Stamped.com"
__license__ = "TODO"

import os, socket, sys

from subprocess import Popen, PIPE
from optparse   import OptionParser

__hostname  = socket.gethostname()
__error     = False

def log(s, error=False):
    global __error
    __error |= error

    print "%s) %s%s" % (__hostname, "WARNING: " if error else "", str(s))

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
        return True
    elif os.path.exists("/etc/init/%s.conf" % name):
        log("%s not running; attempting to start\n" % name, error=True)
        ret = execute("initctl start %s" % name)
        return True
    else:
        return False
    
    if 0 == ret[1]:
        log(ret[0])
    else:
        log("%s failed (%s)\n" % (name, ret[0]), error=True)

def sync_repo(path, force=False, branch=None):
    if branch is None:
        branch = 'master'
        
    cmds = []
    cmds.append("cd %s" % path)
    cmds.append("git checkout %s" % branch)
    if force:
        cmds.append("git reset --hard HEAD")
        cmds.append("git clean -fd")
    cmds.append("git pull")

    cmd = " && ".join(cmds)
    ret = execute(cmd)

    if 0 != ret[1]:
        log("failed to update %s (%s); possibly retry with force to override local changes\n" % (path, ret[0]), error=True)


def parseCommandLine():
    usage    = "Usage: %prog [options]"
    version = "%prog " + __version__
    parser   = OptionParser(usage=usage, version=version)

    parser.add_option("-f", "--force", action="store_true", default=False,
                      help="force cleaning / updating of underlying repositories")
    parser.add_option("-b", "--branch", action="store", default=None,
                      help="git branch to checkout, if not master")
    return parser.parse_args()

def rebuild_fastcompare(stamped):
    python_cmd = 'python ' + os.path.join(stamped, 'platform/resolve/fastcompare_setup.py')
    full_command = ' && '.join(['cd ' + stamped, python_cmd + ' build', python_cmd + ' install'])
    log("Running command: " + full_command)
    ret = execute(full_command)
    if ret[1]:
        log("Failed to build new fastcompare module (%s). Command: %s" % (ret[0], full_command), error=True)

def main():
    options, args   = parseCommandLine()
    bootstrap       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root            = os.path.dirname(bootstrap)
    stamped         = os.path.join(root, "stamped")
    
    repos = [
        (bootstrap, False, False),
        (stamped, True, True),
    ]
    
    for repo, passBranch, enable_force in repos:
        if os.path.exists(repo):
            force = options.force and enable_force
            
            if passBranch:
                sync_repo(repo, force, options.branch)
            else:
                sync_repo(repo, force)
    
    rebuild_fastcompare(stamped)
    
    restart_upstart_daemon("gunicorn_api")
    is_web = restart_upstart_daemon("gunicorn_web")
    restart_upstart_daemon("gunicorn_analytics")
    restart_upstart_daemon("celeryd")
    restart_upstart_daemon("celerybeat")
    restart_upstart_daemon("ratelimiter")
    
    execute("/stamped/stamped/servers/web2/bin/restart.sh")
    sys.exit(1 if __error else 0)

if __name__ == '__main__':
    main()

