#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2012 Stamped.com"
__license__ = "TODO"

import time, os, subprocess, re, sys, boto

from datetime            import datetime
from boto.ec2.connection import EC2Connection
from boto                import utils

AWS_ACCESS_KEY_ID = 'AKIAIXLZZZT4DMTKZBDQ'
AWS_SECRET_KEY = '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'

def backupEBS():
    ec2 = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
    metadata = utils.get_instance_metadata()
    timestamp = str(datetime.utcnow())
        
    try:
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
        
        print 'UUID: %s' % uuid

        # Create EBS Snapshots
        volumes = [v for v in ec2.get_all_volumes() if v.attach_data.instance_id == metadata['instance-id']]
        
        for volume in volumes:
            if len(volume.attach_data.device) == 8:
                description = "Instance: %s | Drive: %s | Time: %s | UUID: %s" % (
                    metadata['instance-id'], 
                    volume.attach_data.device, 
                    timestamp,
                    uuid)
                print '-------------------'
                print 'Begin snapshot (%s):' % datetime.utcnow()
                print 'Volume Id: %s' % volume.id
                print 'Description: "%s"' % description
                ec2.create_snapshot(volume.id, description)
                print 'Success!'
                
        print '-------------------'
    
    except Exception as e:
        print 'EXCEPTION: %s' % e
        exc_type, exc_value, exc_traceback = sys.exc_info()
        f = traceback.format_exception(exc_type, exc_value, exc_traceback)

    finally:
        try:
            # Unlock Mongo
            cmd = "mongo localhost:27017/admin --eval 'printjson(db.$cmd.sys.unlock.findOne());'"
            status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
            if not re.search(r'"ok" : 1', status[0]):
                raise
        except:
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print '!!!!!!!!!!!!!!!!! UNLOCK FAILED !!!!!!!!!!!!!!!!!'
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            sendmail("DB SERVER LOCKED (unlock failed)", str(metadata))

def sendmail(subject, body):
    try:
        ses = boto.connect_ses(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
        ses.send_email('noreply@stamped.com', str(subject), str(body), 'dev@stamped.com', format='text')
    except:
        import string, sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        f = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print string.joinfields(f, '')

def shell(cmd, customEnv=None):
    pp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, env=customEnv)
    
    output = pp.stdout.read().strip()
    status = pp.wait()
    
    return (output, status)

def get_running(cmd):
    return shell("ps -ef | grep '%s' | grep -v grep" % cmd)

def main():
    print 
    print "###### BEGIN EBS BACKUP ######"
    print "Time: %s" % datetime.utcnow()
    
    prog = os.path.basename(sys.argv[0])
    running = get_running(prog)
    
    if len(running[0].split('\n')) > 1:
        msg = "%s already running!" % prog
        sendmail(msg, running)
        
        print msg
        print "Aborting"
    else:
        # Only run if secondary node in replica set
        cmd = "mongo localhost:27017/admin --eval 'printjson(db.isMaster());'"
        status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
        if re.search(r'"ismaster" : false', status[0]) and re.search(r'"secondary" : true', status[0]):
            print "isSecondary: True"
            backupEBS()
        else:
            print "isSecondary: False"
            print "Aborting"
    
    print "###### END EBS BACKUP ######"
    print "Time: %s" % datetime.utcnow()
    print

if __name__ == '__main__':
    main()

