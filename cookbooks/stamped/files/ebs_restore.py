#!/usr/bin/env python

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

BACKUP_FROM_INSTANCE_ID = 'i-d3f843b2'

def createEBS(conn, size, region, snapshot=None):
	return conn.create_volume(size, region, snapshot)

def main():

	conn = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
	
	metadata = utils.get_instance_metadata()
	
	region = metadata['placement']['availability-zone']
	instance_id = metadata['instance-id']
	
	snapshots = []
	drives = []
	maxTimestamp = 0
	for snapshot in conn.get_all_snapshots(owner='self'):
		if snapshot.description != 'N/A' and snapshot.description[10:20] == BACKUP_FROM_INSTANCE_ID:
			data = {}
			data['id'] = snapshot.id
			data['size'] = snapshot.volume_size
			data['drive'] = snapshot.description[30:38]
			data['timestamp'] = snapshot.description[47:73]
			data['uuid'] = snapshot.description[82:117]
			if data['timestamp'] > maxTimestamp:
				maxTimestamp = data['timestamp']
			snapshots.append(data)
			
	for snapshot in snapshots:
		if snapshot['timestamp'] == maxTimestamp:
			drives.append(snapshot)
			uuid = snapshot['uuid']
			
	print drives
	
	for drive in drives:
		# Verify all drives are in the same configuration
		if drive['uuid'] != uuid:
			raise Exception
		
		target = drive['drive']
		vol = createEBS(conn, drive['size'], region, drive['id'])
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
	
	bash = """
		sudo /sbin/mdadm --assemble --auto-update-homehost -u %s --no-degraded /dev/md0
		echo "/dev/mongodb_vg/mongodb_lv /data ext4 defaults,noatime 0 0" | sudo -E tee -a /etc/fstab
		sudo mkdir /data
		sudo mount /data
	""" % (uuid)
	
	os.system(bash)
	
if __name__ == '__main__':
	main()


