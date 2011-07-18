#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, sys, utils
from kitchen import Kitchen
from system import System
from optparse import OptionParser

class PyNode(object):
    def __init__(self, options):
        self.options = options
    
    @utils.lazyProperty
    def config(self):
        configFilePath = self.options.config
        
        try:
            with open(configFilePath, "rb") as fp:
                source = fp.read()
            
            return eval(source)
        except Exception:
            utils.log("Error parsing config file '%s'" % self.options.config)
            utils.printException()
    
    def run(self):
        kitchen = Kitchen()
        kitchen.updateConfig({ "node" : self.config })
        
        if 'cookbook_path' in self.config:
            for path in self.config['cookbook_path']:
                #if "." not in path:
                #    path = os.path.join(os.path.dirname(utils.resolvePath(self.options.config)), path)
                kitchen.addCookbookPath(path)
        
        if 'recipes' in self.config:
            for recipe in self.config['recipes']:
                kitchen.includeRecipe(recipe)
        
        kitchen.run()

def parseCommandLine():
    usage   = "Usage: %prog [options] configfile"
    version = "%prog " + __version__
    parser  = OptionParser(usage=usage, version=version)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        print "Error: must provide a single config file"
        parser.print_help()
        return None
    else:
        options.config = args[0]
    
    return options

def main():
    # initialize system
    system = System.getInstance()
    
    # parse commandline
    options = parseCommandLine()
    if options is None:
        sys.exit(1)
    
    # initialize and run PyNode
    node = PyNode(options)
    node.run()

if __name__ == '__main__':
    main()

