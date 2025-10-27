#!/bin/bash
set -e

echo "🚀 Starting PlantPal Backend..."

# Run database migrations
echo "🔄 Running database migrations..."
python -m alembic upgrade head

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migrations failed!"
    exit 1
fi

# Start the FastAPI server
echo "🌱 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000