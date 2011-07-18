
from pynode.resources import *
from pynode.utils import AttributeDict
import os

# install prerequisites
env.includeRecipe("virtualenv")

path = env.config.node.path
env.cookbooks.virtualenv.VirtualEnv(path) #, site_packages=False)

env.includeRecipe("pip")
env.includeRecipe("libevent")

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

# start wsgi application (flask server)
if 'wsgi' in env.config.node:
    site = env.config.node.wsgi.app
    log  = env.config.node.wsgi.log
    
    Directory(os.path.dirname(log))
    
    Service(name="wsgi_app", 
            start_cmd=". %s && %s %s >& %s&" % (activate, python, site, log))

