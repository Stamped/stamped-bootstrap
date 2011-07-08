#
# Cookbook Name:: flask
# Recipe:: default
# Author:: AJ Christensen <aj@junglist.gen.nz>
#
# Copyright 2008-2009, Opscode, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

include_recipe 'python'

unless node["flask"]["virtualenv"].nil?
  python_virtualenv node["flask"]["virtualenv"] do
    action :create
  end
end

python_pip "flask" do
  virtualenv node["flask"]["virtualenv"] unless node["gunicorn"]["virtualenv"].nil?
  action :install
end

