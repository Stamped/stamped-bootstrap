
from pynode.resources import *
from pynode.utils import AttributeDict
import os

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

# install git repos
if 'git' in env.config.node and 'repos' in env.config.node.git:
    for repo in env.config.node.git.repos:
        repo = AttributeDict(repo)
        Script(name="git.clone.%s" % repo.url, 
               code="git clone %s %s" % (repo.url, repo.path))

activate = env.config.node.path + "/bin/activate"
python = env.config.node.path + "/bin/python"

print env.config.node.roles

if 'db' in env.config.node.roles:
    env.includeRecipe('mongodb')
    
    options = env.config.node.mongodb.options
    log     = env.config.node.mongodb.log
    mongodb = env.config.node.mongodb.config
    
    Directory(os.path.dirname(mongodb.path))
    
    if 'dbpath' in mongodb.content:
        Directory(os.path.dirname(mongodb.content.dbpath))
    
    print str(mongodb)
    
    env.cookbooks.mongodb.MongoDBConfigFile(**mongodb)
    Service(name="mongod", 
            start_cmd="mongod -- --config %s %s >& log" % (mongodb.path, string.joinfields(options, ' ')))

if 'web_server' in env.config.node.roles:
    # start wsgi application (flask server)
    if 'wsgi' in env.config.node:
        site = env.config.node.wsgi.app
        log  = env.config.node.wsgi.log
        
        Directory(os.path.dirname(log))
        
        Service(name="wsgi_app", 
                start_cmd=". %s && %s %s >& %s&" % (activate, python, site, log))

