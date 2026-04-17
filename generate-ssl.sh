#!/bin/bash
# Generate self-signed SSL certificates for sports prediction platform

mkdir -p /etc/nginx/ssl

openssl req -x509 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/self-signed.key \
  -out /etc/nginx/ssl/self-signed.crt \
  -days 365 -nodes \
  -subj "/C=US/ST=California/L=San Francisco/O=Sports Prediction/CN=localhost"

echo "SSL certificates generated successfully"
ls -la /etc/nginx/ssl/
