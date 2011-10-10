# everyday at 2am
0 2 * * * . /stamped/bin/activate && python /stamped/bootstrap/bin/ebs_backup.py >> /stamped/logs/cron.log 2>&1

