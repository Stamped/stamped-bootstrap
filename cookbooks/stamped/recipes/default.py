
from pynode.resources import *
from pynode.utils import AttributeDict
import os, string

# install prerequisites
env.includeRecipe("virtualenv")

path = env.config.node.path
env.cookbooks.virtualenv.VirtualEnv(path) #, site_packages=False)

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
    
    config = env.config.node.replSet
    primary = config.members[0]['host']
    print "Initializing replica set '%s' with primary '%s'" % (config._id, primary)
    
    if ':' in primary:
        primary_host, primary_port = primary.split(':')
    else:
        primary_host, primary_port = (primary, 27017)
    
    os.putenv('STAMPED_MONGODB_HOST', primary_host)
    os.putenv('STAMPED_MONGODB_PORT', primary_port)
    
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

