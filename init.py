#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, sys
from subprocess import Popen, PIPE
from optparse import OptionParser
from config import convert

def shell(cmd):
    pp = Popen(cmd, shell=True, stdout=PIPE)
    status = pp.wait()
    
    return status

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
    # parse commandline
    (options, params) = parseCommandLine()
    
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    params['path'] = path
    
    shell('python config/init.py -t config/templates/instance.py.j2 -o config/generated/instance.py %s' % \
        string.joinfields(('%s=%s' % (param, params[param] for param in params)), ' '))

if __name__ == '__main__':
    main()

