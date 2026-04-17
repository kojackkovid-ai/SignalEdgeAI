#!/bin/bash
# Create database indexes for performance optimization

PSQL_CMD="psql -U postgres -d sports_predictions -c"

echo "=========================================="
echo "📊 Applying Database Performance Indexes"
echo "=========================================="

# Important: Wait for database tables to exist
echo "⏳ Waiting for database tables..."
sleep 5

# Apply indexes
$PSQL_CMD "
CREATE INDEX IF NOT EXISTS idx_predictions_sport_key ON predictions(sport_key);
CREATE INDEX IF NOT EXISTS idx_predictions_event_id ON predictions(event_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_user_predictions_user_id ON user_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_predictions_created_at ON user_predictions(created_at);
"

echo "✅ Database indexes applied successfully!"
