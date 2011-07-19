
from pynode.resources import Package

package = "mongodb"
if env.system.platform != "mac_os_x":
    package = "mongodb-10gen"

Package(package)

