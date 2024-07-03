# Define a variable for the Redis command
install:
	bash install.sh

setup:
	redis-server --port 6379 &
	python3 Display_app/display_app.py &
	python3 Countert_app/flask_demo.py &