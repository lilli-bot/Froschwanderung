python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if command -v redis-server &> /dev/null; then
    REDIS_CMD=$(command -v redis-server)
    echo "Redis is already installed: $REDIS_CMD"
else
    echo "Redis not found, installing..."
    brew install redis
fi