
# everyday at midnight
@daily . /stamped/bin/activate && python /stamped/bootstrap/bin/update_db.py  >> /stamped/logs/cron.log 2>&1

# everyday at midnight
@daily . /stamped/bin/activate && python /stamped/stamped/sites/stamped.com/bin/handle_custom_entities.py  >> /stamped/logs/handle_custom_entities.log 2>&1

