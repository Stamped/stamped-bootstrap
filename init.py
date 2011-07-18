#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, string, sys
from subprocess import Popen, PIPE
from optparse import OptionParser
from config import convert

node_name = ""

def shell(cmd, stdout=False):
    if stdout:
        pp = Popen(cmd, shell=True)
    else:
        pp = Popen(cmd, shell=True, stdout=PIPE)
    status = pp.wait()
    
    return status

def check_shell(cmd, stdout=False):
    print '[%s] %s' % (node_name, cmd)
    
    if 0 != shell(cmd, stdout):
        print 'error running shell command: %s' % cmd
        sys.exit(1)

def parseCommandLine():
    usage   = "Usage: %prog [[param1=value] [param2=value]...]"
    version = "%prog " + __version__
    parser  = OptionParser(usage=usage, version=version)
    
    (options, args) = parser.parse_args()
    
    params = { }
    
    for arg in args:
        if not '=' in arg:
            print "error: invalid param=value arg '%s'" % arg
            parser.print_help()
            sys.exit(1)
        
        (name, value) = arg.split('=')
        params[name] = value
    
    return (options, params)

def main():
    os.chdir(os.path.dirname(__file__))
    
    # parse commandline
    (options, params) = parseCommandLine()
    global node_name
    node_name = params['name']
    
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    params['path'] = path
    
    config_file = "config/generated/instance.py"
    check_shell('python config/convert.py -t config/templates/instance.py.j2 -o %s %s' % \
        (config_file, string.joinfields(('%s=%s' % (k, v) for k, v in params.iteritems()), ' ')))
    
    os.chdir('pynode')
    check_shell('python setup.py build --build-base=/tmp --force')
    check_shell('python setup.py install --force')
    os.chdir('..')
    check_shell('pynode %s' % config_file, True)

if __name__ == '__main__':
    main()

