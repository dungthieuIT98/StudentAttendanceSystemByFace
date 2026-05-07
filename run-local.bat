@echo off
echo === Student Attendance System by Face ===
echo Starting local development server...
echo.

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo   Python found

echo [2/5] Checking virtual environment...
if not exist ".venv" (
    echo   Creating virtual environment...
    python -m venv .venv
)
echo   Virtual environment ready

echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat
echo   Virtual environment activated

echo [4/5] Installing dependencies...
pip install -r requirements.txt --quiet
echo   Dependencies installed

echo [5/5] Running database migrations...
python manage.py migrate --noinput
echo   Database migrations completed

echo.
echo === Starting Django Development Server ===
echo Server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver
