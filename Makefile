PID_FILE = flask.pid
.PHONY: install setup analytics reset_redis enable_logging disable_logging logging_status stop restart

install:
	bash install.sh
	bash dbt_setup.sh

setup:
	redis-server --port 6379 &
	FLASK_APP=flask_app/flask_app.py flask run --port 5001 & echo $$! > $(PID_FILE) &

analytics:
	python3 results/analytics_processing.py
	bash run_dbt.sh

reset_redis:
	curl -X POST http://localhost:5001/reset_counters

enable_logging:
	curl -X POST http://localhost:5001/enable_logging

disable_logging:
	curl -X POST http://localhost:5001/disable_logging

logging_status:
	curl -X POST http://localhost:5001/logging_status

stop:
	@if [ -f $(PID_FILE) ]; then \
		kill `cat $(PID_FILE)`; \
		rm $(PID_FILE); \
		echo "App stopped and PID file removed."; \
	else \
		echo "PID file not found. Is the app running?"; \
	fi

restart:
	make stop
	make setup
