#!/usr/bin/python

__author__    = "Stamped (dev@stamped.com)"
__version__   = "1.0"
__copyright__ = "Copyright (c) 2012 Stamped.com"
__license__   = "TODO"

from pynode.resources   import *
from pynode.source      import *
from pynode.utils       import AttributeDict
from pynode.errors      import Fail
from subprocess         import Popen, PIPE

import os, pickle, string
import pynode.utils

path     = env.config.node.path
conf     = os.path.join(path, "conf")
activate = os.path.join(path, "bin/activate")

AWS_ACCESS_KEY_ID = 'AKIAIXLZZZT4DMTKZBDQ'
AWS_SECRET_KEY    = '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'

def init_daemon(name):
    # note: we use ubuntu upstart as our daemonization utility of choice, and since ubuntu's 
    # apt package installer frequently installs an init.d version of the daemon upon initial 
    # package install, we manually remove it from /etc/init.d and replace it with a roughly 
    # analogous, arguably simpler upstart version in /etc/init
    Execute("cp /stamped/bootstrap/config/templates/%s.upstart.conf /etc/init/%s.conf && start %s" % 
            (name, name, name))

def kill_mongo():
    Execute(r"ps -e | grep mongod | grep -v grep | sed 's/^[ \t]*\([0-9]*\).*/\1/g' | xargs kill -9 || echo test")
    Execute(r"rm -rf /etc/init/mongodb.conf /etc/init.d/mongodb /var/lib/mongodb/journal")

if 'bootstrap' in env.config.node.roles:
    # install prerequisites
    env.includeRecipe("virtualenv")
    
    # copy over some useful bash and vim settings
    # -------------------------------------------
    Execute('cp /stamped/bootstrap/cookbooks/stamped/files/vimrc /etc/vim/vimrc.local')
    Execute('cat /stamped/bootstrap/cookbooks/stamped/files/bash_profile >> /etc/bash.bashrc')
    File(path='/home/ubuntu/.bash_profile', content=StaticFile('stamped/bash_profile'))
    #File(path='/home/ubuntu/.vimrc', content=StaticFile('stamped/vimrc'))
    
    # setup core directories (/stamped root directory, log dir, conf dir, etc.)
    # -------------------------------------------
    Directory(path)
    Directory(conf)
    
    Directory("/stamped/")
    Directory("/stamped/logs")
    
    try:
        Directory(os.path.dirname(env.config.node.mongodb.config.logpath))
        Directory(os.path.dirname(env.config.node.wsgi.log))
    except:
        pass
    
    # install base package dependencies that are referenced by other packages
    # -----------------------------------------------------------------------
    Package("python-dev")
    Package("gcc")
    Package("g++")
    Package("libjpeg62")
    Package("libjpeg62-dev")
    Package("zlib1g-dev")
    Package("libxml2-dev")
    Package("libxslt1-dev")
    Package("python-lxml")
    Package("ntp")
    Package("mdadm")
    Package("lvm2")
    
    env.includeRecipe("pip")
    env.includeRecipe("libevent")
    
    # install rabbitmq-server
    # -----------------------
    cmd = """
    echo 'deb http://www.rabbitmq.com/debian/ testing main' >> /etc/apt/sources.list
    wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
    apt-key add rabbitmq-signing-key-public.asc
    apt-get -y update
    """
    Execute(cmd)
    Package("rabbitmq-server")
    Execute("/etc/init.d/rabbitmq-server stop; rm -f /etc/init.d/rabbitmq-server")
    
    # install memcached and libmemcached
    # ----------------------------------
    Package("memcached")
    Execute("/etc/init.d/memcached stop; rm -f /etc/init.d/memcached")
    
    cmd = """
    wget http://launchpad.net/libmemcached/1.0/1.0.2/+download/libmemcached-1.0.2.tar.gz
    tar -xvf libmemcached-1.0.2.tar.gz
    cd libmemcached-1.0.2
    ./configure
    make && make install
    cd ..
    """
    Execute(cmd)
    
    # install python packages
    # -----------------------
    for package in env.config.node.python.requirements:
        env.cookbooks.pip.PipPackage(package, virtualenv=path)
    
    # initialize boto
    # -----------------------
    
    # copy boto config
    cmd = "cp /stamped/bootstrap/cookbooks/stamped/files/boto.cfg /etc/boto.cfg"
    Execute(r'. %s && %s' % (activate, cmd))
    
    # ensure most recent version of boto is installed
    cmd = "pip install boto"
    Execute(r'. %s && %s' % (activate, cmd))
    cmd = "pip install -U boto"
    Execute(r'. %s && %s' % (activate, cmd))
    
    # install mongodb
    # ---------------
    env.includeRecipe('mongodb')
    kill_mongo()
    
    # install JRE
    # -----------
    Package('openjdk-6-jre-headless')
    
    # install nginx
    # -------------
    
    # TODO (travis): these URL dependencies are very prone to breaking (already happened twice).
    # When we get some cleanup time, find a simpler way (ideally using apt) to install nginx
    cmd = """
    cd %(path)s
    wget 'http://nginx.org/download/nginx-1.0.5.tar.gz'
    tar -xzvf nginx-1.0.5.tar.gz 
    wget 'ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-8.21.tar.gz'
    tar -xzvf pcre-8.21.tar.gz 
    wget 'http://zlib.net/zlib-1.2.6.tar.gz'
    tar -xzvf zlib-1.2.6.tar.gz 
    wget 'http://www.openssl.org/source/openssl-1.0.0d.tar.gz'
    tar -xzvf openssl-1.0.0d.tar.gz
    cd nginx-1.0.5/
    ./configure --with-pcre=../pcre-8.21/ --with-zlib=../zlib-1.2.6/ --with-openssl=../openssl-1.0.0d --with-http_ssl_module
    make
    mv objs/nginx %(path)s/bin/nginx
    cp conf/mime.types %(path)s/bin/
    cd ../
    rm -rf nginx-1.0.5.tar.gz pcre-8.21.tar.gz zlib-1.2.6.tar.gz openssl-1.0.0d.tar.gz pcre-8.21/ zlib-1.2.6/ openssl-1.0.0d/
    mkdir %(path)s/www
    mkdir %(path)s/www/cache
    """ % { 'path': env.config.node.path }
    
    Execute(r'. %s && %s' % (activate, cmd))
    
    # install elasticsearch
    # ---------------------
    elasticsearch_url = "https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.19.0.RC3.tar.gz"
    
    cmd = """
    mkdir -p temp && cd temp
    curl -OL %s
    tar -xvf elasticsearch-* && rm -f elasticsearch-*.tar.gz
    mv elasticsearch-* /usr/local/elasticsearch
    cd .. && rm -rf temp
    """ % elasticsearch_url
    Execute(cmd)
    
    # install StatsD and its dependencies (graphite, carbon, whisper, cairo, node.js)
    # -------------------------------------------------------------------------------
    Package("python-cairo-dev")
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
    
    # notify dependencies that we are done with bootstrap initialization
    # ------------------------------------------------------------------
    ready = '/stamped/bootstrap/bin/ready.py "%s"' % (pickle.dumps(env.config.node.roles))
    Execute(r'. %s && python %s&' % (activate, ready))
else:
    import datetime, json, os, time
    
    from boto.route53.connection    import Route53Connection
    from boto.ec2.connection        import EC2Connection
    from collections                import defaultdict
    
    def get_modified_time(filename):
        return datetime.datetime.fromtimestamp(os.path.getmtime(filename))
    
    def get_local_instance_id():
        # cache instance id locally
        path = os.path.join(os.path.dirname(os.path.abspath('/stamped/bootstrap/')), '.instance.id.txt')
        
        if os.path.exists(path):
            f = open(path, 'r')
            instance_id = f.read()
            f.close()
            
            if len(instance_id) > 1 and instance_id.startswith('i-'):
                return instance_id
        
        ret = _shell('wget -q -O - http://169.254.169.254/latest/meta-data/instance-id')
        
        if 0 != ret[1]:
            return None
        else:
            f = open(path, 'w')
            f.write(ret[0])
            f.close()
            
            return ret[0]
    
    def _shell(cmd, env=None):
        print cmd
        pp = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, env=env)
        delay = 0.01
        
        while pp.returncode is None:
            time.sleep(delay)
            delay *= 2
            if delay > 1:
                delay = 1
            
            pp.poll()
        
        output = pp.stdout.read().strip()
        return (output, pp.returncode)
    
    def get_stack(stack=None):
        if stack is not None:
            stack = stack.lower()
        
        name = '.%s.stack.txt' % ('__local__' if stack is None else stack)
        path = os.path.join(os.path.dirname(os.path.abspath('/stamped/bootstrap/')), name)
        
        if os.path.exists(path):
            modified = get_modified_time(path)
            current  = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
            
            # only try to use the cached config if it's recent enough
            if modified >= current:
                try:
                    f = open(path, 'r')
                    info = json.loads(f.read())
                    f.close()
                    info = AttributeDict(info)
                    if info.instance is not None and len(info.nodes) > 0:
                        info.nodes = map(AttributeDict, info.nodes)
                        return info
                except:
                    print "error getting cached stack info; recomputing"
                    pynode.utils.printException()
        
        conn = EC2Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_KEY)
        
        reservations = conn.get_all_instances()
        instance_id  = get_local_instance_id()
        stacks       = defaultdict(list)
        cur_instance = None
        
        for reservation in reservations:
            for instance in reservation.instances:
                try:
                    if instance.state == 'running':
                        stack_name = instance.tags['stack']
                        
                        node = dict(
                            name=instance.tags['name'], 
                            stack=stack_name, 
                            roles=eval(instance.tags['roles']), 
                            instance_id=instance.id, 
                            public_dns_name=instance.public_dns_name, 
                            private_dns_name=instance.private_dns_name, 
                            private_ip_address=instance.private_ip_address, 
                        )
                        
                        stacks[stack_name].append(node)
                        
                        if stack is None and instance.id == instance_id:
                            stack = stack_name
                            cur_instance = node
                except:
                    pass
        
        info = {
            'instance' : cur_instance, 
            'nodes'    : stacks[stack], 
        }
        
        f = open(path, 'w')
        f.write(json.dumps(info, indent=2))
        f.close()
        
        info = AttributeDict(info)
        info.nodes = map(AttributeDict, info.nodes)
        
        return info
    
    def set_hostname(name):
        cmd = """
        echo '%s' > /etc/hostname; 
        sysctl kernel.hostname='%s'; 
        sed -i 's/localhost/localhost %s/' /etc/hosts; 
        hostname -b -F /etc/hostname || echo "nevermind"
        """ % (name, name, name)
        
        Execute(cmd)
    
    def init_hostname():
        try:
            stack = get_stack()
            name  = "%s_%s" % (stack.instance.stack, stack.instance.name)
            
            if name is not None and len(name) > 0:
                set_hostname(name)
        except:
            pynode.utils.printException()
    
    kill_mongo()
    init_hostname()
    
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
        
        # note: installing mongodb starts a mongod process for some
        # retarded reason, so kill it before starting our own instance
        kill_mongo()
        
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
        
        # start elasticmongo
        init_daemon("elasticmongo")
    
    if 'webServer' in env.config.node.roles:
        init_daemon("nginx_web")
        init_daemon("gunicorn_web")
    
    if 'apiServer' in env.config.node.roles:
        init_daemon("nginx_api")
        init_daemon("gunicorn_api")
        
        Execute("crontab /stamped/bootstrap/bin/cron.api.sh")
    
    if 'work' in env.config.node.roles:
        init_daemon("celeryd")
    
    if 'mem' in env.config.node.roles:
        init_daemon("memcached")
    
    if 'search' in env.config.node.roles:
        init_daemon("elasticsearch")

