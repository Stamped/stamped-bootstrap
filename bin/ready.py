#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os
# from subprocess import Popen, PIPE
# from flask import request, Response, Flask
# 
# app = Flask(__name__)
# 
# @app.route('/')
# def index():
#	  return "initialized"
#  
# if __name__ == '__main__':
#	  app.run(host='0.0.0.0', port=5001, threaded=True)

def main():

	# Run as root!
	bash = """
		apt-get -y install ganglia-monitor
		mkdir /etc/ganglia/conf.d
		mkdir /usr/lib64/ganglia/python_modules
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/gmond.conf /etc/ganglia/gmond.conf
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/modpython.conf /etc/ganglia/conf.d/modpython.conf
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/python_modules/* /usr/lib64/ganglia/python_modules
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/conf.d/* /etc/ganglia/conf.d
		sleep 10
		#ps -e | grep gmond 
		#ps -e | grep gmond | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9
		#gmond
		/etc/init.d/ganglia-monitor restart
	"""
	
	os.system(bash)
	
if __name__ == '__main__':
	main()