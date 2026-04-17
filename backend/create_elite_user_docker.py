#!/usr/bin/env python3
"""
Create Elite User directly in Docker PostgreSQL
Executes SQL INSERT via docker exec
"""

import subprocess
import sys

# SQL statement
sql_statement = """INSERT INTO users
(id, email, username, password_hash, subscription_tier, subscription_start, is_active, created_at, updated_at)
VALUES ('3dc9f07a-7207-4440-b459-d00926264c63', 'sportsai@gmail.com', 'elite_sportsai', '$2b$12$QhaRije.gcecDi8q.nhZhOx4GSMh6UhqRK/kWyRhzJ5z8oxAKUTYC', 'elite', '2026-03-29T03:47:49.379276', true, '2026-03-29T03:47:49.379276', '2026-03-29T03:47:49.379276');"""

def create_user_in_docker():
    """Create user via docker exec"""
    
    # Docker container name from docker-compose.prod.yml
    container_name = "sports-predictions-db-prod"
    
    print("Creating Elite User in Docker PostgreSQL...")
    print()
    
    try:
        # First, check if container exists
        check_cmd = ["docker", "ps", "-a", "--format", "table {{.Names}}"]
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        
        if container_name not in result.stdout:
            print(f"❌ Docker container '{container_name}' not found")
            print()
            print("Available containers:")
            print(result.stdout)
            print()
            print("To start the database, run:")
            print("  docker-compose -f docker-compose.prod.yml up -d")
            return False
        
        print(f"✅ Found container '{container_name}'")
        print()
        
        # Execute the INSERT statement
        docker_exec_cmd = [
            "docker", "exec", container_name,
            "psql", "-U", "postgres", "-d", "sports_predictions_prod",
            "-c", sql_statement
        ]
        
        print(f"Executing SQL in container...")
        result = subprocess.run(docker_exec_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Elite user created successfully!")
            print()
            print(f"INSERT output: {result.stdout.strip()}")
            print()
            print("User Details:")
            print(f"  Email: sportsai@gmail.com")
            print(f"  Password: bonustester11")
            print(f"  Username: elite_sportsai")
            print(f"  Tier: elite")
            print(f"  User ID: 3dc9f07a-7207-4440-b459-d00926264c63")
            return True
        else:
            print(f"❌ Error executing SQL:")
            print(f"Return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_user_in_docker()
    sys.exit(0 if success else 1)
