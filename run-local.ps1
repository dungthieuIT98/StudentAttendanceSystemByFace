# Student Attendance System by Face - Local Run Script
# This script sets up and runs the Django project locally without Docker

$ErrorActionPreference = "Stop"

Write-Host "=== Student Attendance System by Face ===" -ForegroundColor Cyan
Write-Host "Starting local development server..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if .venv exists, create if not
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    Write-Host "  Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
Write-Host "  Virtual environment activated" -ForegroundColor Green

# Install/Update dependencies
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "  Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ERROR: requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Create .env file if not exists
if (-not (Test-Path ".env")) {
    Write-Host "  Creating .env file from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    Write-Host "  .env file created" -ForegroundColor Green
    Write-Host "  NOTE: Update .env for PostgreSQL connection if needed" -ForegroundColor Yellow
}

# Run database migrations
Write-Host "[5/5] Running database migrations..." -ForegroundColor Yellow
python manage.py migrate --noinput
Write-Host "  Database migrations completed" -ForegroundColor Green

# Check database type
$pgHost = $env:POSTGRES_HOST
if ($pgHost) {
    Write-Host "  Database: PostgreSQL ($pgHost:$env:POSTGRES_PORT)" -ForegroundColor Cyan
} else {
    Write-Host "  Database: db.sqlite3 (SQLite)" -ForegroundColor Cyan
}

# Start the development server
Write-Host ""
Write-Host "=== Starting Django Development Server ===" -ForegroundColor Cyan
Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python manage.py runserver
