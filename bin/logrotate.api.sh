/stamped/logs/*.log {
    daily
    size 20mb
    rotate 10
    compress
    delaycompress
    sharedscripts
    postrotate
        kill -USR1 `cat /stamped/logs/nginx_api.pid`
        kill -USR1 `cat /stamped/conf/gunicorn_api.pid`
    endscript
}
