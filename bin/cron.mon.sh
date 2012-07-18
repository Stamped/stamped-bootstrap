MAILTO=""

# Every two minutes: Run email / APNs alerts
*/2 * * * * . /stamped/bin/activate && python /stamped/stamped/platform/alerts/alerts.py >> /stamped/logs/alerts.log

# Every 10 minutes: Update stats
#*/10 * * * * . /stamped/bin/activate && python /stamped/stamped/platform/stats.py --store >> /stamped/logs/stats.log

# Every day at 3:45 am EST: Upgrade custom entities
45 8 * * * . /stamped/bin/activate && python /stamped/stamped/platform/bin/handle_custom_entities.py  >> /stamped/logs/handle_custom_entities.log 2>&1

# Every day at 4:00 am EST: Import new entities
0 9 * * * . /stamped/bin/activate && python /stamped/stamped/platform/bin/import_entities.py  >> /stamped/logs/import_entities.log 2>&1

# Every Wednesday at 4:30 am EST: Update Apple data
30 9 * * 3 . /stamped/bin/activate && python /stamped/stamped/platform/update_apple.py  >> /stamped/logs/update_apple.log 2>&1
