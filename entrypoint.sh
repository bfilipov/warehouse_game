#!/bin/bash
flask db init
flask db migrate
flask db upgrade
gunicorn game:app -b 0.0.0.0:5001 -w 4 --access-logfile /home/game/logs/warehouse-access.log --error-logfile /home/game/logs/warehouse-error.log
