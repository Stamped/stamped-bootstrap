#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

import time, os, subprocess, re
from datetime import datetime
from boto.ec2.connection import EC2Connection
from boto import utils

AWS_ACCESS_KEY_ID = 'AKIAIXLZZZT4DMTKZBDQ'
AWS_SECRET_KEY = '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'

def backupEBS():
    ec2 = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
    metadata = utils.get_instance_metadata()
    
    # Lock Mongo
    cmd = "mongo localhost:27017/admin --eval 'printjson(db.runCommand({fsync:1,lock:1}));'"
    status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
    if not re.search(r'"ok" : 1', status[0]):
        raise Exception('Lock failed')
    
    # Log EBS Volumes
    uuid = 'N/A'
    cmd = 'sudo mdadm --detail /dev/md0'
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
        
        regex = re.compile(r'UUID : ([a-zA-Z0-9:]+)', re.IGNORECASE)
        match = regex.search(str(p))
        if match:
            uuid = match.group().replace('UUID : ', '')
    except:
        uuid = 'N/A'
    
    # Create EBS Snapshots
    timestamp = str(datetime.utcnow())
    volumes = [v for v in ec2.get_all_volumes() if v.attach_data.instance_id == metadata['instance-id']]
    
    for volume in volumes:
        if len(volume.attach_data.device) == 8:
            description = "Instance: %s | Drive: %s | Time: %s | UUID: %s" % (
                metadata['instance-id'], 
                volume.attach_data.device, 
                timestamp,
                uuid)
        
            ec2.create_snapshot(volume.id, description)
    
    # Unlock Mongo
    cmd = "mongo localhost:27017/admin --eval 'printjson(db.$cmd.sys.unlock.findOne());'"
    status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
    if not re.search(r'"ok" : 1', status[0]):
        raise Exception('Unlock failed')

def main():
    # Only run if secondary node in replica set
    cmd = "mongo localhost:27017/admin --eval 'printjson(db.isMaster());'"
    status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
    if re.search(r'"ismaster" : false', status[0]) and re.search(r'"secondary" : true', status[0]):
        backupEBS()

if __name__ == '__main__':
    main()

