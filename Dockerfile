FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=FaceByAttendance.settings.docker

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        libglib2.0-0 \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media

EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["sh", "-c", "\
    echo 'Waiting for database...' && \
    python -c 'import time; time.sleep(5)' && \
    echo 'Running migrations...' && \
    python manage.py migrate --noinput && \
    echo 'Collecting static files...' && \
    python manage.py collectstatic --noinput --clear && \
    echo 'Creating superuser if not exists...' && \
    python -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Admin already exists')\" && \
    echo 'Starting server...' && \
    gunicorn FaceByAttendance.wsgi:application --bind 0.0.0.0:8000 --workers 4"]
