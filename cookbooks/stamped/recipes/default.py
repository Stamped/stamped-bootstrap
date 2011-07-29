
from pynode.resources import *
from pynode.utils import AttributeDict
from pynode.errors import Fail
import os, pickle, string
from subprocess import Popen, PIPE

# install prerequisites
env.includeRecipe("virtualenv")

path = env.config.node.path
Directory(path)

conf = os.path.join(path, "conf")
Directory(conf)

if env.system.platform != "mac_os_x":
    Package("python-dev")
    Package("gcc")
    Package("mdadm")
    Package("lvm2")

env.includeRecipe("pip")
env.includeRecipe("libevent")

# install python packages
for package in env.config.node.python.requirements:
    env.cookbooks.pip.PipPackage(package, virtualenv=path)

if 'db' in env.config.node.roles:
    env.includeRecipe('mongodb')
    
    options = env.config.node.mongodb.options
    config  = env.config.node.mongodb.config
    
    if env.system.platform != "mac_os_x":
        # Setup EBS instances for data
        config.dbpath = "/data/db"
        Script(name="setup EBS", code=StaticFile("ebs_config.py"))
    
    Directory(os.path.dirname(config.logpath))
    Directory(os.path.dirname(config.path))
    Directory(config.dbpath)
    
    env.cookbooks.mongodb.MongoDBConfigFile(**config)
    
    # TODO: where is this rogue mongod process coming from?!
    if env.system.platform != 'mac_os_x':
        Execute(r"ps -e | grep mongod | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9")
    
    Service(name="mongod", 
        start_cmd="mongod --fork --replSet %s --config %s %s" % \
        (config.replSet, config.path, string.joinfields(options, ' ')))

if 'webServer' in env.config.node.roles or 'crawler' in env.config.node.roles:
    if 'git' in env.config.node and 'repos' in env.config.node.git:
        if env.system.platform == "mac_os_x":
            for repo in env.config.node.git.repos:
                repo = AttributeDict(repo)
                Script(name="hack", 
                       code="ln -s %s %s" % ("/Users/fisch0920/dev/stamped", repo.path))
        else:
            # install git repos
            for repo in env.config.node.git.repos:
                repo = AttributeDict(repo)
                Script(name="git.clone.%s" % repo.url, 
                       code="git clone %s %s" % (repo.url, repo.path))
    
if 'webServer' in env.config.node.roles:
    activate = env.config.node.path + "/bin/activate"
    
    # start wsgi application (flask server)
    if 'wsgi' in env.config.node:
        site = env.config.node.wsgi.app
        log  = env.config.node.wsgi.log
        
        Directory(os.path.dirname(log))
        
        # TODO: use /bin/bash as default interpreter? this bourne shell redirection 
        # syntax blows and is incompatible with the default redirection syntax on bash
        # under mac os x
        #if env.system.platform == "mac_os_x":
        #    Service(name="wsgi_app", 
        #            start_cmd=". %s && python %s >& %s &" % (activate, site, log))
        #else:
        #    Service(name="wsgi_app", 
        #            start_cmd=". %s && python %s > %s 2>&1 &" % (activate, site, log))

