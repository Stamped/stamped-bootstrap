#!/usr/bin/env python

"""
REQUIRES:
sudo apt-get install mdadm
sudo apt-get install lvm2

"""

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import time, os, subprocess
from datetime import datetime
from boto.ec2.connection import EC2Connection
from boto import utils

AWS_ACCESS_KEY_ID = 'AKIAIXLZZZT4DMTKZBDQ'
AWS_SECRET_KEY = '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'

def createEBS(conn, size, region, snapshot=None):
	return conn.create_volume(size, region, snapshot)

def main():

	metadata = utils.get_instance_metadata()
	
	region = metadata['placement']['availability-zone']
	instance_id = metadata['instance-id']
	size = 8 # in GB
	drives = ['sdf', 'sdg', 'sdh', 'sdi']

	conn = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
	
	for drive in drives:
		target = '/dev/%s' % (drive)
		vol = createEBS(conn, size, region)
		time.sleep(5)
		
		while True:
			try:
				vol.attach(instance_id, target)
				break
			except:
				time.sleep(5)
		
		while True:
			if os.path.exists(target):
				break
			else:
				time.sleep(5)

	# Build bash command to run			 
	bash = ''
	for drive in drives:
		bash += '\n echo ",,L" | sudo sfdisk /dev/' + drive
	bash += '\n'
	bash += 'sleep 10 \n' ## Not sure if this is necessary.
	bash += 'sudo /sbin/mdadm /dev/md0 --create --level=10 --raid-devices=' + str(len(drives))
	for drive in drives:
		bash += ' /dev/' + drive + '1'
	bash += '\n '
	bash += 'sleep 10 \n' ## Not sure if this is necessary, either.
	bash += 'sudo /sbin/pvcreate /dev/md0 \n'
	bash += 'sudo /sbin/vgcreate -s 64M mongodb_vg /dev/md0 \n'
	bash += 'sudo /sbin/lvcreate -l ' + str(size * 1000 / 64) + ' -nmongodb_lv mongodb_vg \n'
	bash += 'sudo /sbin/mkfs.ext4 /dev/mongodb_vg/mongodb_lv \n'
	
	bash += 'echo "/dev/mongodb_vg/mongodb_lv /data ext4 defaults,noatime 0 0" | sudo -E tee -a /etc/fstab \n'
	bash += 'sudo mkdir /data \n'
	bash += 'sudo mount /dev/mongodb_vg/mongodb_lv /data \n'
	
	print bash
	
	os.system(bash)
	
if __name__ == '__main__':
	main()
	
	