#!/bin/bash

# Quick Deployment Setup Script
# Run this to prepare for production deployment

set -e

echo "🚀 Sports Prediction Platform - Production Deployment Setup"
echo "=========================================================="

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found. Creating from template..."
    cp .env.example .env.production
    echo "✅ Created .env.production - EDIT THIS FILE with your values!"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Install from https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not installed"
    exit 1
fi
echo "✅ Docker Compose found: $(docker-compose --version)"

# Validate .env.production
echo ""
echo "📋 Checking environment variables..."
required_vars=("DB_PASS" "SECRET_KEY" "ODDS_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" .env.production; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "⚠️  Missing variables in .env.production:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "📝 Edit .env.production and fill in missing values"
fi

# Build check
echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env.production with your actual values"
echo "   2. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "   3. Check status: docker-compose -f docker-compose.prod.yml ps"
echo "   4. View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🌐 For Railway.app deployment, see PRODUCTION_DEPLOYMENT_GUIDE.md"
