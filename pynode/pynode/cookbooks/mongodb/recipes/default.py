
from pynode import *
#from pynode.resources import Package

package = "mongodb"

if env.system.platform != "mac_os_x":
    Execute("sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10",
        not_if = "(apt-key list | grep 10gen.com > /dev/null)")
    
    Execute("sudo echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' >> /etc/apt/sources.list")
    package = "mongodb-10gen"

Package(package)

