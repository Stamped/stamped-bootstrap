DESCRIPTION
====

Installs flask in a virtualenv and runs it on a single site as a service.

REQUIREMENTS
====

Cookbooks
----

* python

Platform
----

Debian or Ubuntu though may work where 'build-essential' works, but other platforms are untested.

ATTRIBUTES
====

All node attributes are set under the `flask` namespace.

*TODO*

USAGE
====

*TODO*
# Example
    
    # create a config with the default values
    flask_config "/etc/flask/myapp.py" do
      action :create
    end
    
    # tweak some worker related values...we're web scale baby
    flask_config "/etc/flask/myapp.py" do
      debug true
      action :create
    end

LICENSE and AUTHOR
====

Author:: Travis Fischer (<travis@stamped.com>)

Copyright:: 2011, Stamped, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
