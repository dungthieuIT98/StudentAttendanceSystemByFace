# Docker Management Script for Windows PowerShell
# Usage: .\docker-manage.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Docker Management Commands" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Basic:" -ForegroundColor Yellow
    Write-Host "  .\docker-manage.ps1 up              - Start all services"
    Write-Host "  .\docker-manage.ps1 down            - Stop all services"
    Write-Host "  .\docker-manage.ps1 restart         - Restart all services"
    Write-Host "  .\docker-manage.ps1 logs            - View all logs"
    Write-Host "  .\docker-manage.ps1 status          - Show status"
    Write-Host ""
    Write-Host "Django:" -ForegroundColor Yellow
    Write-Host "  .\docker-manage.ps1 shell           - Django shell"
    Write-Host "  .\docker-manage.ps1 migrate         - Run migrations"
    Write-Host "  .\docker-manage.ps1 createsuperuser - Create superuser"
    Write-Host ""
    Write-Host "Database:" -ForegroundColor Yellow
    Write-Host "  .\docker-manage.ps1 backup          - Backup database"
    Write-Host "  .\docker-manage.ps1 pgadmin         - Start with pgAdmin"
    Write-Host ""
    Write-Host "Other:" -ForegroundColor Yellow
    Write-Host "  .\docker-manage.ps1 build           - Build images"
    Write-Host "  .\docker-manage.ps1 clean           - Remove all (WARNING!)"
    Write-Host ""
}

switch ($Command.ToLower()) {
    "help" {
        Show-Help
    }
    "build" {
        Write-Host "Building Docker images..." -ForegroundColor Green
        docker-compose build
    }
    "up" {
        Write-Host "Starting all services..." -ForegroundColor Green
        docker-compose up -d
        Write-Host "Services started!" -ForegroundColor Green
        Write-Host "Access at: http://localhost:8000" -ForegroundColor Cyan
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker-compose down
    }
    "restart" {
        Write-Host "Restarting all services..." -ForegroundColor Yellow
        docker-compose restart
    }
    "status" {
        docker-compose ps
    }
    "logs" {
        docker-compose logs -f
    }
    "shell" {
        Write-Host "Opening Django shell..." -ForegroundColor Green
        docker-compose exec web python manage.py shell
    }
    "migrate" {
        Write-Host "Running migrations..." -ForegroundColor Green
        docker-compose exec web python manage.py migrate
    }
    "createsuperuser" {
        Write-Host "Creating superuser..." -ForegroundColor Green
        docker-compose exec web python manage.py createsuperuser
    }
    "backup" {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "backup_$timestamp.sql"
        Write-Host "Creating backup: $backupFile..." -ForegroundColor Green
        docker-compose exec -T db pg_dump -U postgres face_attendance > $backupFile
        Write-Host "Backup completed!" -ForegroundColor Green
    }
    "pgadmin" {
        Write-Host "Starting with pgAdmin..." -ForegroundColor Green
        docker-compose --profile tools up -d
        Write-Host "pgAdmin: http://localhost:5050" -ForegroundColor Cyan
    }
    "clean" {
        Write-Host "WARNING: This will remove all containers and volumes!" -ForegroundColor Red
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            docker-compose down -v
            Write-Host "Cleaned!" -ForegroundColor Green
        } else {
            Write-Host "Cancelled." -ForegroundColor Yellow
        }
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
