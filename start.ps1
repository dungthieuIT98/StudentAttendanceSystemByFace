# Script khoi dong Django dev server
# Chay:
#   .\start.ps1            # mac dinh: auto-reload (khuyen nghi khi dev UI)
#   .\start.ps1 -NoReload  # tat auto-reload (neu can)

param(
  [switch]$NoReload
)

$env:POSTGRES_DB       = 'face_attendance'
$env:POSTGRES_USER     = 'postgres'
$env:POSTGRES_PASSWORD = 'postgres'
$env:POSTGRES_HOST     = '127.0.0.1'
$env:POSTGRES_PORT     = '15432'
$env:DEBUG             = '1'
$env:DJANGO_SECRET_KEY = 'change-me'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:PYTHONUNBUFFERED  = '1'

$python = "C:\Users\hvhus\.venvs\face-attendance\Scripts\python.exe"

Write-Host "Dang kiem tra DB Docker..." -ForegroundColor Cyan
docker compose up -d db | Out-Null

Write-Host "Khoi dong Django tai http://127.0.0.1:8000/" -ForegroundColor Green
if ($NoReload) {
  & $python manage.py runserver --noreload
} else {
  & $python manage.py runserver
}
