PID_FILE = flask.pid
.PHONY: install setup analytics reset_redis enable_logging disable_logging logging_status stop restart metabase

# Install dependencies
install:
	bash install.sh
	bash dbt_setup.sh

# Start the Flask app and the Redis server
setup:
	redis-server --port 6379 &
	FLASK_APP=flask_app/flask_app.py flask run --port 5001 & echo $$! > $(PID_FILE) &

# After a session, process the event log files to Parquet and run the DBT job
analytics:
	python3 results/analytics_processing.py
	bash run_dbt.sh

# Start the Metabase container for data visualisation
metabase:
	docker compose up -d -f ./analytics/duckdb/docker-compose.yml

# Reset the Redis cache used for the Froschteich live display
reset_redis:
	curl -X POST http://localhost:5001/reset_counters

# Enable click logging
enable_logging:
	curl -X POST http://localhost:5001/enable_logging

# disable click logging e.g. for function test
disable_logging:
	curl -X POST http://localhost:5001/disable_logging

# display whether click logging currently is enabled
logging_status:
	curl -X POST http://localhost:5001/logging_status

# Shut down the Flask app based on the PID stored in the PID_FILE
stop:
	@if [ -f $(PID_FILE) ]; then \
		kill `cat $(PID_FILE)`; \
		rm $(PID_FILE); \
		echo "App stopped and PID file removed."; \
	else \
		echo "PID file not found. Is the app running?"; \
	fi

# Restart the Flask app
restart:
	make stop
	make setup
