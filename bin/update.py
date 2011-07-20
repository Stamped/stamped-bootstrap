#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, utils

def main():
    bootstrap = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.dirname(bootstrap)
    stamped = os.path.join(root, "stamped")
    
    repos = [
        bootstrap, 
        stamped
    ]
    
    for repo in repos:
        if os.path.exists(repo):
            utils.shell("cd %s && git pull" % repo)

if __name__ == '__main__':
    main()

