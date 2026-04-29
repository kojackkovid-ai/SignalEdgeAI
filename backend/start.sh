#!/bin/sh
set -e

echo "=========================================="
echo "Starting Sports Prediction API"
echo "=========================================="

# Print environment variables for debugging
echo ""
echo "Configuration:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_PORT: $DB_PORT"
echo "  DB_USER: $DB_USER"
echo "  API_HOST: $API_HOST"
echo "  API_PORT: $API_PORT"
echo ""

# Run startup verification (non-fatal for database connection delays)
echo "Running startup verification..."
python check_startup.py || echo "⚠️  Startup verification had issues (will retry during API initialization)"

echo ""
echo "Starting API server on $API_HOST:${API_PORT:-8000}..."
exec python -m uvicorn app.main:app --host "$API_HOST" --port "${API_PORT:-8000}"
