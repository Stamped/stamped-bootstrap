#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import os, pickle
from optparse import OptionParser

def ganglia(roles=None):
		
	# Run as root!
	bash = """
		apt-get -y install ganglia-monitor
		mkdir /etc/ganglia/conf.d
		mkdir /usr/lib64/ganglia/python_modules
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/gmond.conf /etc/ganglia/gmond.conf
		cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/modpython.conf /etc/ganglia/conf.d/modpython.conf
	"""
	
	if roles != None:
		if 'db' in roles:
			bash += """
				cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/python_modules/* /usr/lib64/ganglia/python_modules
				cp /stamped/bootstrap/cookbooks/stamped/files/ganglia/conf.d/* /etc/ganglia/conf.d
			"""
			
	bash += """
		sleep 5
		/etc/init.d/ganglia-monitor restart
	"""
	print bash
	os.system(bash)
	

def parseCommandLine():
	usage	= "Usage: %prog [options] command [args]"
	version = "%prog " + __version__
	parser	= OptionParser(usage=usage, version=version)
	
	(options, args) = parser.parse_args()
	try:
		roles = pickle.loads(args[0])
	except:
		roles = None
	return roles

def main():
	# parse commandline
	ganglia(parseCommandLine())

if __name__ == '__main__':
	main()