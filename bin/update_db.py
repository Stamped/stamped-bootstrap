#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os
from subprocess import Popen

def main():
    sources = [
        "fandango", 
        "amazonbookfeed", 
    ]
    
    activate = "/stamped/bin/activate"
    crawler  = "/stamped/stamped/sites/stamped.com/bin/crawler"
    top      = "/stamped/stamped/sites/stamped.com/bin"
    log = open("/stamped/logs/update_db.log", "a")
    
    for source in sources:
        cmd = ". %s && cd %s && python crawler.py -s merge %s" % (activate, crawler, source)
        
        Popen(cmd, shell=True, stdout=log, stderr=log).wait()
    
    log.close()
    
    log = open("/stamped/logs/update_apple.log", "a")
    cmd = ". %s && cd %s && python update_apple.py" % (activate, top)
    Popen(cmd, shell=True, stdout=log, stderr=log).wait()
    log.close()

if __name__ == '__main__':
    main()

