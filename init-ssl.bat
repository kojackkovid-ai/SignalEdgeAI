@echo off
REM SSL Certificate Setup Script for Sports Prediction Platform (Windows)
REM This script initializes Let's Encrypt SSL certificates

setlocal enabledelayedexpansion

set "DOMAIN=%~1"
set "EMAIL=%~2"

if "%DOMAIN%"=="" set "DOMAIN=localhost"
if "%EMAIL%"=="" set "EMAIL=admin@example.com"

echo ==========================================
echo Sports Prediction Platform - SSL Setup
echo ==========================================
echo Domain: %DOMAIN%
echo Email: %EMAIL%
echo.

REM Create directories
if not exist "certbot\conf" mkdir certbot\conf
if not exist "certbot\www" mkdir certbot\www

REM Check if certificates already exist
if exist "certbot\conf\live\%DOMAIN%" (
    echo [OK] SSL certificates already exist for %DOMAIN%
    echo      Location: certbot\conf\live\%DOMAIN%
    goto :done
)

echo Checking for development setup...

if "%DOMAIN%"=="localhost" goto :dev_ssl
if "%DOMAIN%"=="127.0.0.1" goto :dev_ssl

echo Setting up Let's Encrypt certificates...
echo This requires your domain to be publicly accessible.
echo.

REM For production with Let's Encrypt
docker-compose down nginx 2>nul
docker run --rm ^
  -v %cd%\certbot\conf:/etc/letsencrypt ^
  -v %cd%\certbot\www:/var/www/certbot ^
  -p 80:80 ^
  certbot/certbot certonly ^
  --standalone ^
  --non-interactive ^
  --agree-tos ^
  --email %EMAIL% ^
  -d %DOMAIN%

if errorlevel 1 (
    echo [ERROR] Failed to obtain Let's Encrypt certificate
    echo Please verify:
    echo.  1. Domain resolves to this server
    echo.  2. Ports 80/443 are accessible
    echo.  3. Email address is valid
    goto :error
)

echo [OK] Let's Encrypt certificate obtained successfully!
REM Update Nginx config for Let's Encrypt
powershell -Command "(Get-Content nginx\conf.d\default.conf) -replace 'your-domain.com', '%DOMAIN%' | Set-Content nginx\conf.d\default.conf"
echo [OK] Nginx configuration updated for domain: %DOMAIN%
goto :done

:dev_ssl
echo Setting up self-signed certificate for development...
if not exist "nginx\ssl" mkdir nginx\ssl

if not exist "nginx\ssl\self-signed.crt" (
    echo Generating self-signed certificate...
    openssl req -x509 -newkey rsa:4096 -keyout nginx\ssl\self-signed.key -out nginx\ssl\self-signed.crt -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=%DOMAIN%"
    echo [OK] Self-signed certificate created
) else (
    echo [OK] Self-signed certificate already exists
)

REM Update Nginx config for development
echo Updating Nginx configuration for self-signed certificates...
powershell -Command "^
  $content = Get-Content 'nginx\conf.d\default.conf'; ^
  $content = $content -replace 'ssl_certificate /etc/letsencrypt', '# ssl_certificate /etc/letsencrypt'; ^
  $content = $content -replace 'ssl_certificate_key /etc/letsencrypt', '# ssl_certificate_key /etc/letsencrypt'; ^
  $content = $content -replace '# ssl_certificate /etc/nginx', 'ssl_certificate /etc/nginx'; ^
  $content = $content -replace '# ssl_certificate_key /etc/nginx', 'ssl_certificate_key /etc/nginx'; ^
  Set-Content 'nginx\conf.d\default.conf' $content ^
"

echo [OK] Development SSL setup complete!
echo.
echo Note: Using self-signed certificates. For production, use Let's Encrypt.

:done
echo.
echo ==========================================
echo SSL Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Run: docker-compose up -d
echo   2. Access: https://localhost (development) or https://%DOMAIN% (production)
echo   3. Check logs: docker logs sports-predictions-nginx
echo.
goto :end

:error
echo.
echo ==========================================
echo SSL Setup Failed
echo ==========================================
exit /b 1

:end
endlocal
