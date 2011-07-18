#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, string, sys
from subprocess import Popen, PIPE
from optparse import OptionParser
from config import convert

def shell(cmd):
    pp = Popen(cmd, shell=True, stdout=PIPE)
    status = pp.wait()
    
    return status

def check_shell(cmd):
    if 0 != shell(cmd):
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
    
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    params['path'] = path
    
    config_file = "config/generated/instance.py"
    check_shell('python config/convert.py -t config/templates/instance.py.j2 -o %s %s' % \
        (config_file, string.joinfields(('%s=%s' % (k, v) for k, v in params.iteritems()), ' ')))
    
    check_shell('pynode/setup.py build install')
    check_shell('pynode %s' % config_file)

if __name__ == '__main__':
    main()

