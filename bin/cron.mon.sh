*/2 * * * * . /stamped/bin/activate && python /stamped/stamped/sites/stamped.com/bin/alerts/alerts.py >> /stamped/logs/alerts.log

*/10 * * * * . /stamped/bin/activate && python /stamped/stamped/sites/stamped.com/bin/stats.py --store >> /stamped/logs/stats.log

