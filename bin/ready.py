#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os
from subprocess import Popen, PIPE
from flask import request, Response, Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "initialized"
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)

