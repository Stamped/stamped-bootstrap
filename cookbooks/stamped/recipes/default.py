
from pynode.resources import *
from pynode.source import *
from pynode.utils import AttributeDict
from pynode.errors import Fail
import os, pickle, string
from subprocess import Popen, PIPE

if env.system.platform != "mac_os_x":
    # copy over some useful bash and vim settings
    File(path='/home/ubuntu/.bash_profile', 
         content=StaticFile('stamped/bash_profile'))
    File(path='/home/ubuntu/.vimrc', 
         content=StaticFile('stamped/vimrc'))

# install prerequisites
env.includeRecipe("virtualenv")

path = env.config.node.path
Directory(path)

conf = os.path.join(path, "conf")
Directory(conf)

if env.system.platform != "mac_os_x":
    Package("python-dev")
    Package("gcc")
    Package("libjpeg62")
    Package("libjpeg62-dev")
    Package("python-lxml")
    
    if 'db' in env.config.node.roles:
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
    restore = env.config.node.raid.restore
    ebs     = env.config.node.raid.config
    
    if env.system.platform != "mac_os_x":
        # Setup EBS instances for data
        config.dbpath = "/data/db"
        f = '/stamped/bootstrap/cookbooks/stamped/files/ebs_config.py'
        if restore:
            Execute('chmod +x %s  && %s -r %s' % (f, f, restore))
        else:
            Execute('chmod +x %s  && %s' % (f, f))

        # Up ulimit to 16384
        Execute('ulimit -n 16384')
    
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
        system_stamped_path = None
        if env.system.platform == "mac_os_x":
            system_stamped_path = "/Users/fisch0920/dev/stamped"
        
        # install git repos
        for repo in env.config.node.git.repos:
            repo = AttributeDict(repo)
            
            if system_stamped_path is not None:
                Script(name="hack", 
                       code="ln -s %s %s" % (system_stamped_path, repo.path))
            else:
                Script(name="git.clone.%s" % repo.url, 
                       code="git clone %s %s" % (repo.url, repo.path))
        else:
            for repo in env.config.node.git.repos:
                repo = AttributeDict(repo)

if 'webServer' in env.config.node.roles:
    activate = env.config.node.path + "/bin/activate"

    if 'wsgi' in env.config.node:

        cmd = """
        cd %(path)s
        wget 'http://nginx.org/download/nginx-1.0.5.tar.gz'
        tar -xzvf nginx-1.0.5.tar.gz 
        wget 'ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-8.10.tar.gz'
        tar -xzvf pcre-8.10.tar.gz 
        wget 'http://zlib.net/zlib-1.2.5.tar.gz'
        tar -xzvf zlib-1.2.5.tar.gz 
        wget 'http://www.openssl.org/source/openssl-1.0.0d.tar.gz'
        tar -xzvf openssl-1.0.0d.tar.gz
        cd nginx-1.0.5/
        ./configure --with-pcre=../pcre-8.10/ --with-zlib=../zlib-1.2.5/ --with-openssl=../openssl-1.0.0d --with-http_ssl_module
        make
        mv objs/nginx %(path)s/bin/nginx
        cp conf/mime.types %(path)s/bin/
        cd ../
        rm -rf nginx-1.0.5.tar.gz pcre-8.10.tar.gz zlib-1.2.5.tar.gz openssl-1.0.0d.tar.gz pcre-8.10/ zlib-1.2.5/ openssl-1.0.0d/
        """ % { 'path': env.config.node.path }

        Execute(r'. %s && %s' % (activate, cmd))
    
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

activate = env.config.node.path + "/bin/activate"
ready = '/stamped/bootstrap/bin/ready.py "%s"' % (pickle.dumps(env.config.node.roles))

Execute(r'. %s && python %s&' % (activate, ready))

