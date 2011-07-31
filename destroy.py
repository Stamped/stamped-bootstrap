#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, pickle, string, sys
from subprocess import Popen, PIPE
from optparse import OptionParser
from config import convert

node_name = ""

def shell(cmd, stdout=False):
    if stdout:
        pp = Popen(cmd, shell=True)
    else:
        pp = Popen(cmd, shell=True, stdout=PIPE)
        output = pp.stdout.read()
    
    status = pp.wait()
    return status

def check_shell(cmd, stdout=False, show_cmd=True):
    if show_cmd:
        print '[%s] %s' % (node_name, cmd)
    
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin/activate")
    if os.path.exists(path):
        cmd = ". %s && %s" % (path, cmd)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    ret = shell(cmd, stdout)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    if 0 != ret:
        print 'error running shell command: %s' % cmd
        sys.exit(1)

def parseCommandLine():
    usage   = "Usage: %prog pickled-params"
    version = "%prog " + __version__
    parser  = OptionParser(usage=usage, version=version)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    
    params = pickle.loads(args[0])
    return (options, params)

def main():
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    
    # parse commandline
    (options, params) = parseCommandLine()
    
    global node_name
    node_name = params['name']
    params['path'] = os.path.dirname(path)
    
    config_file = "config/generated/destroy.py"
    check_shell('python config/convert.py -t config/templates/destroy.py.j2 -o %s "%s"' % \
        (config_file, pickle.dumps(params)), show_cmd=False)
    
    check_shell('pynode %s' % config_file, stdout=True)

if __name__ == '__main__':
    main()

