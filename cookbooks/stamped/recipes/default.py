
from pynode.resources import *
from pynode.utils import AttributeDict
from pynode.errors import Fail
import os, pickle, string

# install prerequisites
env.includeRecipe("virtualenv")

path = env.config.node.path
env.cookbooks.virtualenv.VirtualEnv(path) #, site_packages=False)

conf = os.path.join(path, "conf")
Directory(conf)

if env.system.platform != "mac_os_x":
    Package("python-dev")
    Package("gcc")

env.includeRecipe("pip")
#env.includeRecipe("libevent")

# install python packages
for package in env.config.node.python.requirements:
    env.cookbooks.pip.PipPackage(package, virtualenv=path)

if 'db' in env.config.node.roles:
    env.includeRecipe('mongodb')
    
    options = env.config.node.mongodb.options
    config  = env.config.node.mongodb.config
    
    Directory(os.path.dirname(config.logpath))
    Directory(os.path.dirname(config.path))
    Directory(config.dbpath)
    
    env.cookbooks.mongodb.MongoDBConfigFile(**config)
    Service(name="mongod", 
            start_cmd="mongod --config %s %s&" % \
            (config.path, string.joinfields(options, ' ')))

if 'replSetInit' in env.config.node.roles:
    assert 'replSet' in env.config.node
    from pymongo import Connection
    from pymongo.errors import *
    from pprint import pprint
    from time import sleep
    
    replSet = env.config.node.replSet
    
    if env.system.platform != "mac_os_x":
        from boto.ec2.connection import EC2Connection
        stackName = env.config.node.stack_name
        aws_access_key_id = env.config.node.aws_access_key_id
        aws_access_key_secret = env.config.node.aws_access_key_secret
        
        dbInstances = []
        webInstances = []
        
        conn = EC2Connection(aws_access_key_id, aws_access_key_secret)
        reservations = conn.get_all_instances()
        stackNameKey = 'aws:cloudformation:stack-name'
        stackFamilyKey = 'stamped:family'
        
        for reservation in reservations:
            for instance in reservation.instances:
                if stackNameKey in instance.tags and instance.tags[stackNameKey].lower() == stackName:
                    if instance.tags[stackFamilyKey].lower() == 'Database':
                        dbInstances.append(instance.private_dns_name)
                    if instance.tags[stackFamilyKey].lower() == 'WebServer':
                        webInstances.append(instance.private_dns_name)
        
        if len(dbInstances) > 1: # Only run if multiple instances exist
            replSetMembers = []
            for i in range(len(dbInstances)):
                replSetMembers.append({"_id": i, "host": dbInstances[i]})
            
            config = {"_id": replSet._id, "memebers": replSetMembers}
        else:
            raise Fail("invalid number of db instances")
    else:
        config = env.config.node.replSet
    
    if len(config.members) > 0:
        primary = config.members[0]['host']
        print "Initializing replica set '%s' with primary '%s'" % (config._id, primary)
        
        if ':' in primary:
            primary_host, primary_port = primary.split(':')
        else:
            primary_host, primary_port = (primary, 27017)
        
        conf = {
            'mongodb' : {
                'host' : primary_host, 
                'port' : int(primary_port), 
            }
        }
        
        conf_str = pickle.dumps(conf)
        conf_path = os.getenv('STAMPED_CONF_PATH')
        if conf_path is None:
            raise Fail("must define a valid STAMPED_CONF_PATH")
        
        File(conf_path, 
             content=conf_str)
        
        conn = Connection(primary, slave_okay=True)
        try:
            conn.admin.command({'replSetInitiate' : dict(config)})
        except AutoReconnect:
            sleep(1)
            pass
        
        initializing = True
        while initializing:
            try:
                status = conn.admin.command({'replSetGetStatus' : 1})
                pprint(status)
                initializing = False
            except (AutoReconnect, OperationFailure):
                sleep(1)
                pass

if 'web_server' in env.config.node.roles:
    # install git repos
    if 'git' in env.config.node and 'repos' in env.config.node.git:
        for repo in env.config.node.git.repos:
            repo = AttributeDict(repo)
            Script(name="git.clone.%s" % repo.url, 
                   code="git clone %s %s" % (repo.url, repo.path))
    
    activate = env.config.node.path + "/bin/activate"
    python = env.config.node.path + "/bin/python"
    
    # start wsgi application (flask server)
    if 'wsgi' in env.config.node:
        site = env.config.node.wsgi.app
        log  = env.config.node.wsgi.log
        
        Directory(os.path.dirname(log))
        
        Service(name="wsgi_app", 
                start_cmd=". %s && %s %s >& %s&" % (activate, python, site, log))
    
    # populate the replica set with some initial, sample data
    if 'replSetInit' in env.config.node.roles:
        Execute("python %s" % env.config.node.populateDB, 
                delayed=True)

