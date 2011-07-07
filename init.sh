
echo "script initiated as `whoami`"

echo "deb http://apt.opscode.com/ `lsb_release -cs`-0.10 main" | tee /etc/apt/sources.list.d/opscode.list
echo "1"

wget -qO - http://apt.opscode.com/packages@opscode.com.gpg.key | apt-key add -

apt-get update

apt-get -y install chef

echo "chef installed"