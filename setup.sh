#!/bin/bash

# Development setup script for Linux/Mac

set -e

echo "🚀 Sports Prediction Platform - Development Setup"
echo "=================================================="

# Check prerequisites
echo "📦 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 20+ is required"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required"
    exit 1
fi

echo "✓ All prerequisites installed"

# Setup backend
echo -e "\n🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install -r requirements.txt
echo "✓ Backend dependencies installed"

# Copy env file
if [ ! -f ".env" ]; then
    cp ../.env.example .env
    echo "✓ Created .env file (update with your settings)"
fi

cd ..

# Setup frontend
echo -e "\n🎨 Setting up frontend..."
cd frontend

npm install
echo "✓ Frontend dependencies installed"

cd ..

# Start services
echo -e "\n🐳 Starting Docker services..."
docker-compose up -d
echo "✓ Services started"

# Wait for database
echo "⏳ Waiting for database..."
sleep 5

# Run migrations
echo -e "\n🔄 Running database migrations..."
cd backend
source venv/bin/activate
python -m alembic upgrade head
cd ..
echo "✓ Migrations complete"

echo -e "\n✅ Setup complete!"
echo -e "\nNext steps:"
echo "1. Update .env files with your configuration"
echo "2. Start backend:  cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:5173 in your browser"
