# Define a variable for the Redis command
install:
	bash install.sh

setup:
	redis-server --port 6379 &
	python3 Display_app/display_app.py &
	python3 Countert_app/flask_demo.py &

reset_redis:
	curl -X POST http://localhost:5001/reset_counters

enable_logging:
	curl -X POST http://localhost:5001/enable_logging

disable_logging:
	curl -X POST http://localhost:5001/disable_logging

logging_status:
	curl -X POST http://localhost:5001/logging_status
