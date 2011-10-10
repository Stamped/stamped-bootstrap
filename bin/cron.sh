
# everyday at midnight
@daily . /stamped/bin/activate && python /stamped/bootstrap/bin/update_db.py  >> /stamped/logs/cron.log 2>&1

