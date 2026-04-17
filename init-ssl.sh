#!/bin/bash

# SSL Certificate Setup Script for Sports Prediction Platform
# This script initializes Let's Encrypt SSL certificates

DOMAIN="${1:-localhost}"
EMAIL="${2:-admin@example.com}"

echo "=========================================="
echo "Sports Prediction Platform - SSL Setup"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Create directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Check if certificates already exist
if [ -d "./certbot/conf/live/$DOMAIN" ]; then
    echo "✓ SSL certificates already exist for $DOMAIN"
    echo "  Location: ./certbot/conf/live/$DOMAIN"
    exit 0
fi

echo "Checking for existing placeholder certificates..."

# For development: create self-signed certificate if needed
if [ "$DOMAIN" = "localhost" ] || [ "$DOMAIN" = "127.0.0.1" ]; then
    echo "Setting up self-signed certificate for development..."
    
    mkdir -p ./nginx/ssl
    
    if [ ! -f "./nginx/ssl/self-signed.crt" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout ./nginx/ssl/self-signed.key -out ./nginx/ssl/self-signed.crt -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        echo "✓ Self-signed certificate created at ./nginx/ssl/"
    else
        echo "✓ Self-signed certificate already exists"
    fi
    
    # Update Nginx config for development
    echo "Updating Nginx configuration for self-signed certificates..."
    sed -i 's|ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;|# ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;|' ./nginx/conf.d/default.conf
    sed -i 's|ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;|# ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;|' ./nginx/conf.d/default.conf
    sed -i 's|# ssl_certificate /etc/nginx/ssl/self-signed.crt;|ssl_certificate /etc/nginx/ssl/self-signed.crt;|' ./nginx/conf.d/default.conf
    sed -i 's|# ssl_certificate_key /etc/nginx/ssl/self-signed.key;|ssl_certificate_key /etc/nginx/ssl/self-signed.key;|' ./nginx/conf.d/default.conf
    
    echo "✓ Development SSL setup complete!"
    echo ""
    echo "Note: Using self-signed certificates. For production, use Let's Encrypt."
    
else
    # Production: use Let's Encrypt
    echo "Setting up Let's Encrypt certificates..."
    
    # Stop Nginx if running to free up port 80
    docker-compose down nginx 2>/dev/null || true
    
    # Get certificate using Certbot
    docker run --rm \
        -v ./certbot/conf:/etc/letsencrypt \
        -v ./certbot/www:/var/www/certbot \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN"
    
    if [ $? -eq 0 ]; then
        echo "✓ Let's Encrypt certificate obtained successfully!"
        
        # Update Nginx config for Let's Encrypt
        sed -i "s|your-domain.com|$DOMAIN|g" ./nginx/conf.d/default.conf
        
        echo "✓ Nginx configuration updated for domain: $DOMAIN"
    else
        echo "✗ Failed to obtain Let's Encrypt certificate"
        echo "Please check:"
        echo "  1. Domain resolves to this server"
        echo "  2. Ports 80/443 are accessible"
        echo "  3. Email address is valid"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "SSL Setup Instructions:"
echo "=========================================="
echo ""
echo "1. For Development (self-signed):"
echo "   ./init-ssl.sh"
echo ""
echo "2. For Production (Let's Encrypt):"
echo "   ./init-ssl.sh your-domain.com your-email@example.com"
echo ""
echo "3. Start services:"
echo "   docker-compose up -d"
echo ""
echo "4. Access your application:"
echo "   https://your-domain.com"
echo ""
echo "5. Check certificate status:"
echo "   docker logs sports-predictions-certbot"
echo ""
echo "=========================================="
