
from pynode.resources import Script, Service

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
        Script(name="git.clone." % repo.url, 
               code="git clone %s %s" % (repo.url, repo.path))

"""
activate = env.config.node.path + "/bin/activate"
python = env.config.node.path + "/bin/python"
site = env.config.node.wsgi_app
wsgi_log = env.config.node.wsgi_log

Service(name="wsgi_app", 
        start_cmd="source %s && %s %s >& %s&" % (activate, python, site, wsgi_log))
"""

