#!/usr/bin/env python3
import bcrypt
import uuid
from datetime import datetime

# Generate hash for password 'bonustester11'
password = 'bonustester11'
password_bytes = password.encode('utf-8')
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password_bytes, salt)
hash_str = hashed.decode('utf-8')

user_id = str(uuid.uuid4())
email = 'sportsai@gmail.com'
username = 'elite_sportsai'
now = datetime.utcnow().isoformat()

print("SQL INSERT Statement:")
print("=" * 80)
print()
print("INSERT INTO users")
print("(id, email, username, password_hash, subscription_tier, subscription_start, is_active, created_at, updated_at)")
print(f"VALUES ('{user_id}', '{email}', '{username}', '{hash_str}', 'elite', '{now}', true, '{now}', '{now}');")
print()
print("=" * 80)
print()
print("User Details:")
print(f"  User ID: {user_id}")
print(f"  Email: {email}")
print(f"  Username: {username}")
print(f"  Password: {password}")
print(f"  Tier: elite")
print(f"  Password Hash: {hash_str}")
print()
print("To apply this:")
print("  1. If using Docker: docker exec -it sports-predictions-db-prod psql -U postgres -d sports_predictions_prod")
print("     Then paste the INSERT statement above")
print()
print("  2. If using local psql: psql -U postgres -d sports_predictions_prod")
print("     Then paste the INSERT statement above")
print()
print("  3. Or connect via graphical tool like pgAdmin and execute the statement")
