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
    
    """
    for arg in args:
        if not '=' in arg:
            print "error: invalid param=value arg '%s'" % arg
            parser.print_help()
            sys.exit(1)
        
        (name, value) = arg.split('=')
        params[name] = value
    """
    
    return (options, params)

def main():
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    
    if os.path.exists(os.path.join(path, "bin")):
        shell('rm -rf %s/bin %s/install %s/lib' % (path, path, path))
    
    # parse commandline
    (options, params) = parseCommandLine()
    assert 'name' in params
    
    global node_name
    node_name = params['name']
    params['path'] = os.path.dirname(path)
    
    from pprint import pprint
    pprint(params)
    
    check_shell('easy_install virtualenv', True)
    check_shell('virtualenv . && . bin/activate')
    check_shell('pip install -U Jinja2')
    
    config_file = "config/generated/instance.py"
    check_shell('python config/convert.py -t config/templates/instance.py.j2 -o %s "%s"' % \
        (config_file, pickle.dumps(params)), show_cmd=False)
    #string.joinfields(('%s=%s' % (k, v) for k, v in params.iteritems()), ' ')))
    
    os.chdir('pynode')
    check_shell('python setup.py build --build-base=/tmp --force')
    check_shell('python setup.py install --force --record=.pynode.record')
    check_shell('rm -rf `cat .pynode.record`')
    check_shell('python setup.py install --force')
    os.chdir(path)
    check_shell('pynode %s' % config_file, True)

if __name__ == '__main__':
    main()

