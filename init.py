#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, pickle, string, sys
from subprocess import Popen, PIPE
from optparse import OptionParser
from config import convert
import utils

node_name = ""
virtualenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin/activate")

def get_virtualenv_bin_path():
    global virtualenv_path
    return os.path.join(virtualenv_path, "bin/activate")

def check_shell(cmd, stdout=False, show_cmd=True):
    if show_cmd:
        print '[%s] %s' % (node_name, cmd)
    
    path = get_virtualenv_bin_path()
    if os.path.exists(path):
        cmd = ". %s && %s" % (path, cmd)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    ret = utils.shell(cmd, stdout)
    
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
    
    import json
    params = json.loads(args[0].replace("'", '"'))
    
    return (options, params)

def main():
    global virtualenv_path
    path = os.path.dirname(os.path.abspath(__file__))
    virtualenv_path = os.path.dirname(path)
    os.chdir(path)
    
    if os.path.exists(os.path.join(virtualenv_path, "bin")):
        # remove virtualenv if it previously exists for some reason
        # otherwise, the virtualenv creation step will fail
        utils.shell('rm -rf %s/bin %s/install %s/lib' % (virtualenv_path, virtualenv_path, virtualenv_path))
    
    # parse commandline
    (options, params) = parseCommandLine()
    assert 'name' in params
    
    global node_name
    node_name = params['name']
    params['path'] = virtualenv_path
    
    os.putenv('STAMPED_ROOT', params['path'])
    os.putenv('STAMPED_CONF_PATH', os.path.join(virtualenv_path, 'conf/stamped.conf'))
    
    from pprint import pprint
    pprint(params)
    
    check_shell('easy_install virtualenv', True)
    check_shell('virtualenv %s && . %s/bin/activate' % (virtualenv_path, virtualenv_path))
    check_shell('pip install -U Jinja2')
    
    config_file = "config/generated/instance.py"
    check_shell('python config/convert.py -t config/templates/instance.py.j2 -o %s "%s"' % \
        (config_file, pickle.dumps(params)), show_cmd=False)
    
    os.chdir('pynode')
    check_shell('python setup.py build --build-base=/tmp --force')
    check_shell('python setup.py install --force --record=.pynode.record')
    check_shell('rm -rf `cat .pynode.record`')
    check_shell('python setup.py install --force')
    os.chdir(path)
    check_shell('pynode %s' % config_file, True)

if __name__ == '__main__':
    main()

