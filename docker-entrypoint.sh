#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Student Attendance System - Starting${NC}"
echo -e "${GREEN}=====================================${NC}"

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
    
    max_retries=30
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="${POSTGRES_DB:-face_attendance}",
        user="${POSTGRES_USER:-postgres}",
        password="${POSTGRES_PASSWORD:-postgres}",
        host="${POSTGRES_HOST:-db}",
        port="${POSTGRES_PORT:-5432}"
    )
    conn.close()
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
        then
            echo -e "${GREEN}PostgreSQL is ready!${NC}"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        echo -e "${YELLOW}PostgreSQL is unavailable - attempt $retry_count/$max_retries${NC}"
        sleep 2
    done
    
    echo -e "${RED}PostgreSQL did not become ready in time${NC}"
    exit 1
}

# Wait for database to be ready
wait_for_db

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}Migrations completed!${NC}"

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}Static files collected!${NC}"

# Create superuser if doesn't exist (optional)
echo -e "${YELLOW}Checking for superuser...${NC}"
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser 'admin' created with password 'admin123'")
else:
    print("Superuser already exists")
END

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Starting application...${NC}"
echo -e "${GREEN}=====================================${NC}"

# Execute the main command
if [ "$1" = "gunicorn" ]; then
    exec gunicorn FaceByAttendance.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-4} \
        --threads ${GUNICORN_THREADS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-50} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${GUNICORN_LOG_LEVEL:-info}
elif [ "$1" = "runserver" ]; then
    exec python manage.py runserver 0.0.0.0:8000
else
    exec "$@"
fi
