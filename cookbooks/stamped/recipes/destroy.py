
import os, sys
from subprocess import Popen, PIPE

def shell(cmd):
    pp = Popen(cmd, shell=True, stdout=PIPE)
    output = pp.stdout.read().strip()
    status = pp.wait()
    
    return status

def check_shell(cmd, show_cmd=True):
    if show_cmd:
        print cmd
     
    ret = shell(cmd)
    if 0 != ret:
        print "error running shell cmd %s" % cmd
        sys.exit(1)

if 'db' in env.config.node.roles:
    check_shell(r"ps -e | grep mongod | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9")

if 'webServer' in env.config.node.roles or 'apiServer' in env.config.node.roles:
    if 'wsgi' in env.config.node:
        check_shell(r"ps -e | grep python | grep 'serve\.py' | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9")

