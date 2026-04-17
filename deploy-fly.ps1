# Automated Fly.io Deployment Script
# Usage: .\deploy-fly.ps1

param(
    [string]$AppName = "sports-predictions-ai",
    [string]$Region = "ord",
    [switch]$SkipAuth = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Fly.io Deployment Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if flyctl is installed
try {
    $version = flyctl version
    Write-Host "✓ flyctl installed: $version" -ForegroundColor Green
}
catch {
    Write-Host "✗ flyctl not found. Please install from: https://fly.io/docs/getting-started/installing-flyctl/" -ForegroundColor Red
    exit 1
}

# Authenticate
if (-not $SkipAuth) {
    Write-Host ""
    Write-Host "Authenticating with Fly.io..." -ForegroundColor Yellow
    flyctl auth login
}

# Get current auth status
$whoami = flyctl auth whoami 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Authenticated as: $whoami" -ForegroundColor Green
}
else {
    Write-Host "✗ Not authenticated. Run: flyctl auth login" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting deployment of $AppName in region $Region..." -ForegroundColor Cyan

# Step 1: Create or launch app
Write-Host ""
Write-Host "Step 1: Creating Fly app..." -ForegroundColor Yellow
$appExists = flyctl apps list --json 2>$null | ConvertFrom-Json | Where-Object { $_.Name -eq $AppName }

if ($appExists) {
    Write-Host "✓ App $AppName already exists" -ForegroundColor Green
}
else {
    Write-Host "Creating new app $AppName..." -ForegroundColor Cyan
    flyctl launch --name $AppName --region $Region --builder docker --no-deploy
}

# Step 2: Create PostgreSQL
Write-Host ""
Write-Host "Step 2: Creating PostgreSQL database..." -ForegroundColor Yellow
$dbName = "$($AppName)-db"
$dbExists = flyctl postgres list --json 2>$null | ConvertFrom-Json | Where-Object { $_.Name -eq $dbName }

if ($dbExists) {
    Write-Host "✓ Database $dbName already exists" -ForegroundColor Green
    $attachExists = flyctl postgres list --json 2>$null | ConvertFrom-Json | Where-Object { $_.Name -eq $dbName -and $_.AppID -eq $AppName }
    if (-not $attachExists) {
        Write-Host "Attaching database to app..." -ForegroundColor Cyan
        flyctl postgres attach $dbName --app $AppName --yes
    }
}
else {
    Write-Host "Creating PostgreSQL database..." -ForegroundColor Cyan
    flyctl postgres create `
        --name $dbName `
        --region $Region `
        --initial-cluster-size 1 `
        --vm-size shared-cpu-1x
    
    Write-Host "Attaching PostgreSQL to app..." -ForegroundColor Cyan
    flyctl postgres attach $dbName --app $AppName --yes
}

# Step 3: Create Redis
Write-Host ""
Write-Host "Step 3: Creating Redis database..." -ForegroundColor Yellow
$redisName = "$($AppName)-redis"
$redisExists = flyctl redis list --json 2>$null | ConvertFrom-Json | Where-Object { $_.Name -eq $redisName }

if ($redisExists) {
    Write-Host "✓ Redis $redisName already exists" -ForegroundColor Green
    $attachExists = flyctl redis list --json 2>$null | ConvertFrom-Json | Where-Object { $_.Name -eq $redisName }
    if (-not $attachExists) {
        Write-Host "Attaching Redis to app..." -ForegroundColor Cyan
        flyctl redis attach $redisName --app $AppName --yes
    }
}
else {
    Write-Host "Creating Redis database..." -ForegroundColor Cyan
    flyctl redis create `
        --name $redisName `
        --region $Region `
        --eviction-policy allkeys-lru
    
    Write-Host "Attaching Redis to app..." -ForegroundColor Cyan
    flyctl redis attach $redisName --app $AppName --yes
}

# Step 4: Set secrets
Write-Host ""
Write-Host "Step 4: Setting environment secrets..." -ForegroundColor Yellow

$secretKey = openssl rand -hex 32
Write-Host "Generated SECRET_KEY (first 16 chars): $($secretKey.Substring(0,16))..." -ForegroundColor Cyan

flyctl secrets set `
    SECRET_KEY=$secretKey `
    ENVIRONMENT="production" `
    ENABLE_ANALYTICS="true" `
    SLOT_BASED_RECOMMENDATIONS="true" `
    LOG_LEVEL="INFO" `
    --app $AppName

Write-Host "✓ Secrets set" -ForegroundColor Green

# Step 5: Deploy
Write-Host ""
Write-Host "Step 5: Deploying application..." -ForegroundColor Yellow
Write-Host "This may take 2-5 minutes..." -ForegroundColor Cyan
flyctl deploy --app $AppName

# Step 6: Check status
Write-Host ""
Write-Host "Step 6: Checking deployment status..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
flyctl status --app $AppName

# Get app URL
Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""

$appInfo = flyctl info --app $AppName 2>$null
Write-Host "App URL: https://$AppName.fly.dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test health endpoint:"
Write-Host "   curl https://$AppName.fly.dev/health"
Write-Host ""
Write-Host "2. View logs (real-time):"
Write-Host "   flyctl logs --app $AppName -f"
Write-Host ""
Write-Host "3. Add custom domain (optional):"
Write-Host "   flyctl certs create your-domain.com --app $AppName"
Write-Host ""
Write-Host "Documentation: https://fly.io/docs/" -ForegroundColor Gray
