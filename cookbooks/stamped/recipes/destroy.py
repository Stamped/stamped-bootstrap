
import os

if 'db' in env.config.node.roles:
    # TODO: temporary
    os.system("ps -e | grep mongod | grep -v grep | sed 's/^\([0-9]*\).*/\1/g' | xargs kill -9")

if 'web_server' in env.config.node.roles:
    # start wsgi application (flask server)
    if 'wsgi' in env.config.node:
        # TODO
        os.system("ps -e | grep python | grep 'serve\.py' | grep -v grep | sed 's/^\([0-9]*\).*/\1/g' | xargs kill -9")

