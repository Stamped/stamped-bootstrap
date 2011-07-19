
from pynode import *
#from pynode.resources import Package

package = "mongodb"
if env.system.platform != "mac_os_x":
    package = "mongodb-10gen"

Package(package)

###

Package("mongodb-stable")

if env.config.mongodb.nodefault:
    Service("mongodb")
    File(env.config.mongodb.configpath,
        action = "delete",
        notifies = [("stop", env.resources["Service"]["mongodb"], True)])
    File("/etc/init/mongodb.conf", action="delete")
    File("/etc/init.d/mongodb", action="delete")
else:
    Directory(env.config.mongodb.dbpath,
        owner = "mongodb",
        group = "mongodb",
        mode = 0755,
        recursive = True)

    Service("mongodb")

    File("/etc/init/mongodb.conf",
        owner = "root",
        group = "root",
        mode = 0644,
        content = Template("mongodb/upstart.conf.j2", variables=dict(mongodb=env.config.mongodb)),
        notifies = [
            ("restart", env.resources["Service"]["mongodb"], True),
        ])

    File(env.config.mongodb.configpath,
        owner = "root",
        group = "root",
        mode = 0644,
        content = Template("mongodb/mongodb.conf.j2", variables=dict(mongodb=env.config.mongodb)),
        notifies = [("restart", env.resources["Service"]["mongodb"])])
