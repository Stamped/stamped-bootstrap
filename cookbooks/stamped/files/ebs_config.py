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

import time, os, subprocess, sys, traceback
from datetime import datetime
from optparse import OptionParser
from boto.ec2.connection import EC2Connection
from boto import utils

AWS_ACCESS_KEY_ID = 'AKIAIXLZZZT4DMTKZBDQ'
AWS_SECRET_KEY = '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'

def createEBS(conn, size, region, snapshot=None):
    return conn.create_volume(size, region, snapshot)

def printException():
    """
        Simple debug utility to print a stack trace.
    """
    #traceback.print_exc()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    #traceback.print_exception(exc_type, exc_value, exc_traceback,
    #                          limit=8, file=sys.stderr)
    f = traceback.format_exception(exc_type, exc_value, exc_traceback)
    f = ''.join(f)
    sys.stderr.write(f)
    sys.stderr.flush()

def config():
    metadata = utils.get_instance_metadata()
    
    region = metadata['placement']['availability-zone']
    instance_id = metadata['instance-id']
    size = 64 # in GB
    drives = ['sdf', 'sdg', 'sdh', 'sdi' ]
    
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
                printException()
                time.sleep(5)
        
        while True:
            if os.path.exists(target):
                break
            else:
                printException()
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
    
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.temp.sh')
    cmd = '/bin/bash -c %s' % path
    f=open(path, 'w')
    f.write(cmd)
    f.close()
    os.system('chmod +x %s' % path)
    """

def restore(instance):
    conn = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
    metadata = utils.get_instance_metadata()
    
    region = metadata['placement']['availability-zone']
    instance_id = metadata['instance-id']
    
    snapshots = []
    drives = []
    maxTimestamp = 0
    
    for snapshot in conn.get_all_snapshots(owner='self'):
        if snapshot.description != 'N/A' and snapshot.description[10:20] == instance:
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
        sudo chown root /data/db
        sudo rm /data/db/mongod.lock
    """ % (uuid)
    
    os.system(bash)

def parseCommandLine():
    usage   = "Usage: %prog [options] command [args]"
    version = "%prog " + __version__
    parser  = OptionParser(usage=usage, version=version)
    
    parser.add_option("-r", "--restore", action="store", dest="restore", 
        default=None, type="string", help="Instance ID to restore snapshot from")
    
    (options, args) = parser.parse_args()
    args = map(lambda arg: arg.lower(), args)
    
    return (options, args)

def main():
    # parse commandline
    (options, args) = parseCommandLine()
    
    if options.restore != None:
        restore(options.restore)
    else:
        config()

if __name__ == '__main__':
    main()

