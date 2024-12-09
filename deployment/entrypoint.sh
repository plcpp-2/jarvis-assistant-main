#!/bin/bash
set -e

# Wait for dependencies
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST 6379; do
    sleep 1
done
echo "Redis is up"

echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST 5432; do
    sleep 1
done
echo "PostgreSQL is up"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start Prometheus metrics exporter
echo "Starting metrics exporter..."
python -m prometheus_client &

# Start the application
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting Jarvis Assistant in production mode..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
else
    echo "Starting Jarvis Assistant in development mode..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi
