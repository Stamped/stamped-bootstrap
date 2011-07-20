import sys
from subprocess import Popen, PIPE

def shell(cmd, stdout=False):
    if stdout:
        pp = Popen(cmd, shell=True)
    else:
        pp = Popen(cmd, shell=True, stdout=PIPE)
        output = pp.stdout.read()
    status = pp.wait()
    
    return status

def write(filename, content):
    f = open(filename, "w")
    f.write(content)
    f.close()

