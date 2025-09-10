#!/bin/bash
set -e

echo "🚀 Starting Crypto DeFi Analyzer..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run Alembic migrations
echo "🔄 Running Alembic migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migrations failed!"
    exit 1
fi

# Start the application based on environment
if [ "$DEV_MODE" = "true" ]; then
    echo "🔧 Starting in development mode..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
else
    echo "🏭 Starting in production mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS:-2} \
        --log-level warning \
        --no-access-log
fi