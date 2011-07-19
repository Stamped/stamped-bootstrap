
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
    # TODO: temporary
    check_shell("ps -e | grep mongod | grep -v grep | sed 's/^\([0-9]*\).*/\1/g' | xargs kill -9")

if 'web_server' in env.config.node.roles:
    # start wsgi application (flask server)
    if 'wsgi' in env.config.node:
        # TODO
        check_shell("ps -e | grep python | grep 'serve\.py' | grep -v grep | sed 's/^\([0-9]*\).*/\1/g' | xargs kill -9")

