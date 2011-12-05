
### ALL CRON JOBS RUNNING ON MON

# Every day at 3:45 am EST
# 45 8 * * * . /stamped/bin/activate && python /stamped/stamped/sites/stamped.com/bin/handle_custom_entities.py  >> /stamped/logs/handle_custom_entities.log 2>&1

# Every day at 4:00 am EST 
# 0 9 * * * . /stamped/bin/activate && python /stamped/bootstrap/bin/update_db.py  >> /stamped/logs/cron.log 2>&1

# Every Wednesday at 4:30 am EST
# 30 9 * * 3 . /stamped/bin/activate && python /stamped/stamped/sites/stamped.com/bin/update_apple.py  >> /stamped/logs/update_apple.log 2>&1

