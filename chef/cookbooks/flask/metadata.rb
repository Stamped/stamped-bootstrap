maintainer        "Stamped, Inc."
maintainer_email  "dev@stamped.com"
license           "Apache 2.0"
description       "Installs and configures Flask"
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version           "1.0.0"

%w{ python }.each do |cb|
  depends cb
end

