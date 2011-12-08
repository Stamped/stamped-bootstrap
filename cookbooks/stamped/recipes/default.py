
from pynode.resources import *
from pynode.source import *
from pynode.utils import AttributeDict
from pynode.errors import Fail

import os, pickle, string
from subprocess import Popen, PIPE

path     = env.config.node.path
conf     = os.path.join(path, "conf")
activate = os.path.join(path, "bin/activate")

def init_daemon(name):
    Execute("cp /stamped/bootstrap/config/templates/%s.upstart.conf /etc/init/%s.conf && start %s" % 
            (name, name, name))

if 'bootstrap' in env.config.node.roles:
    # install prerequisites
    env.includeRecipe("virtualenv")
    
    Directory(path)
    Directory(conf)
    
    Execute('cp /stamped/bootstrap/cookbooks/stamped/files/vimrc /etc/vim/vimrc.local')
    Execute('cat /stamped/bootstrap/cookbooks/stamped/files/bash_profile >> /etc/bash.bashrc')
    
    try:
        Directory(os.path.dirname(env.config.node.mongodb.config.logpath))
        Directory(os.path.dirname(env.config.node.wsgi.log))
    except:
        pass
    
    Directory("/stamped/")
    Directory("/stamped/logs")
    
    if env.system.platform != "mac_os_x":
        # copy over some useful bash and vim settings
        File(path='/home/ubuntu/.bash_profile', content=StaticFile('stamped/bash_profile'))
        #File(path='/home/ubuntu/.vimrc', content=StaticFile('stamped/vimrc'))
        
        Package("python-dev")
        Package("gcc")
        Package("libjpeg62")
        Package("libjpeg62-dev")
        Package("zlib1g-dev")
        Package("libxml2-dev")
        Package("libxslt1-dev")
        Package("python-lxml")
        Package("ntp")
        Package("mdadm")
        Package("lvm2")
        
        cmd = """
        echo 'deb http://www.rabbitmq.com/debian/ testing main' >> /etc/apt/sources.list
        wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
        apt-key add rabbitmq-signing-key-public.asc
        apt-get -y update
        """
        Execute(cmd)
        Package("rabbitmq-server")
        Execute("/etc/init.d/rabbitmq-server stop; rm -f /etc/init.d/rabbitmq-server")
    
    env.includeRecipe("pip")
    env.includeRecipe("libevent")
    
    # install python packages
    for package in env.config.node.python.requirements:
        env.cookbooks.pip.PipPackage(package, virtualenv=path)
    
    # Copy Boto config
    cmd = "cp /stamped/bootstrap/cookbooks/stamped/files/boto.cfg /etc/boto.cfg"
    Execute(r'. %s && %s' % (activate, cmd))
    
    # Ensure most recent version of boto is installed
    cmd = "pip install boto"
    Execute(r'. %s && %s' % (activate, cmd))
    cmd = "pip install -U boto"
    Execute(r'. %s && %s' % (activate, cmd))
    
    env.includeRecipe('mongodb')
    
    # install JRE
    Package('openjdk-6-jre-headless')
    
    # install nginx
    cmd = """
    cd %(path)s
    wget 'http://nginx.org/download/nginx-1.0.5.tar.gz'
    tar -xzvf nginx-1.0.5.tar.gz 
    wget 'ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-8.13.tar.gz'
    tar -xzvf pcre-8.13.tar.gz 
    wget 'http://zlib.net/zlib-1.2.5.tar.gz'
    tar -xzvf zlib-1.2.5.tar.gz 
    wget 'http://www.openssl.org/source/openssl-1.0.0d.tar.gz'
    tar -xzvf openssl-1.0.0d.tar.gz
    cd nginx-1.0.5/
    ./configure --with-pcre=../pcre-8.13/ --with-zlib=../zlib-1.2.5/ --with-openssl=../openssl-1.0.0d --with-http_ssl_module
    make
    mv objs/nginx %(path)s/bin/nginx
    cp conf/mime.types %(path)s/bin/
    cd ../
    rm -rf nginx-1.0.5.tar.gz pcre-8.13.tar.gz zlib-1.2.5.tar.gz openssl-1.0.0d.tar.gz pcre-8.13/ zlib-1.2.5/ openssl-1.0.0d/
    mkdir %(path)s/www
    mkdir %(path)s/www/cache
    """ % { 'path': env.config.node.path }
    
    Execute(r'. %s && %s' % (activate, cmd))
    
    # install StatsD and its dependencies (graphite, carbon, whisper, cairo, node.js)
    Package("python-cairo-dev")
    Package("g++")
    env.cookbooks.pip.PipPackage("django-tagging", virtualenv=path)
    
    cmd = """
    mkdir -p temp && cd temp
    
    wget http://launchpad.net/graphite/0.9/0.9.9/+download/graphite-web-0.9.9.tar.gz
    wget http://launchpad.net/graphite/0.9/0.9.9/+download/carbon-0.9.9.tar.gz
    wget http://launchpad.net/graphite/0.9/0.9.9/+download/whisper-0.9.9.tar.gz
    wget http://nodejs.org/dist/node-v0.4.12.tar.gz
    
    tar -xvf graphite-web-0.9.9.tar.gz
    tar -xvf whisper-0.9.9.tar.gz
    tar -xvf carbon-0.9.9.tar.gz
    tar -xvf node-v0.4.12.tar.gz
    
    mv carbon-0.9.9  carbon
    mv whisper-0.9.9 whisper
    mv graphite-web-0.9.9 graphite
    mv node-v0.4.12 node
    
    rm -f carbon-0.9.9.tar.gz whisper-0.9.9.tar.gz graphite-web-0.9.9.tar.gz node-v0.4.12.tar.gz
    
    cd whisper  && sudo python setup.py install && cd ..
    cd carbon   && sudo python setup.py install && cd ..
    
    cp /stamped/bootstrap/config/templates/carbon.conf /opt/graphite/conf
    cp /stamped/bootstrap/config/templates/storage-schemas.conf /opt/graphite/conf
    cp /stamped/bootstrap/config/templates/statsd.conf /stamped/conf
    
    cd graphite && sudo python setup.py install && cd ..
    cd node && ./configure --without-ssl && make && make install
    """
    
    Execute(r'. %s && %s' % (activate, cmd))
    
    ready = '/stamped/bootstrap/bin/ready.py "%s"' % (pickle.dumps(env.config.node.roles))
    Execute(r'. %s && python %s&' % (activate, ready))
else:
    Execute(r"ps -e | grep mongod | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9 || echo test")
    
    # clone git repo
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
    
    if 'db' in env.config.node.roles:
        env.includeRecipe('mongodb')
        
        # note: installing mongodb seems to start a mongod process for some
        # retarded reason, so kill it before starting our own instance
        Execute(r"ps -e | grep mongod | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9 || echo test")
        
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
            Execute('echo "* hard nofile 16384" >> /etc/security/limits.conf')
        
        Directory(os.path.dirname(config.path))
        Directory(config.dbpath)
        
        env.cookbooks.mongodb.MongoDBConfigFile(**config)
        
        Service(name="mongod", 
                start_cmd="mongod --fork --replSet %s --config %s %s" % \
                (config.replSet, config.path, string.joinfields(options, ' ')))
        
        # initialize db-specific cron jobs (e.g., backup)
        Execute("crontab /stamped/bootstrap/bin/cron.db.sh")
    
    if 'monitor' in env.config.node.roles:
        cmd = """
        cd /opt/graphite
        echo DEBUG = True >> webapp/graphite/local_settings.py
        PYTHONPATH=`pwd`/whisper ./bin/carbon-cache.py start
        
        cd /opt/graphite
        PYTHONPATH=`pwd`/webapp:`pwd`/whisper python ./webapp/graphite/manage.py syncdb
        PYTHONPATH=`pwd`/webapp:`pwd`/whisper python ./webapp/graphite/manage.py syncdb
        """
        
        Execute(r'. %s && %s' % (activate, cmd))
        
        # start statsd aggregator
        init_daemon("statsd")
        
        # start graphite web server
        init_daemon("graphite")
        
        # start monitoring daemon
        init_daemon("stampedmon")
        
        # start rabbit message queuing server
        init_daemon("rabbitmq-server")
        
        # initialize mon-specific cron jobs (e.g., alerts)
        Execute("crontab /stamped/bootstrap/bin/cron.mon.sh")
    
    if 'webServer' in env.config.node.roles:
        init_daemon("nginx_web")
        init_daemon("gunicorn_web")
    
    if 'apiServer' in env.config.node.roles:
        init_daemon("nginx_api")
        init_daemon("gunicorn_api")
        
        Execute("crontab /stamped/bootstrap/bin/cron.api.sh")
    
    if 'work' in env.config.node.roles:
        pass
        # TODO: test this!
        
        #init_daemon("celeryd")

