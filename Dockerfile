FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=FaceByAttendance.settings.docker

WORKDIR /app

# System libraries needed by psycopg2, OpenCV-headless, TF, etc.
# libgl1-mesa-glx was removed in Debian trixie; opencv-headless does not need OpenGL
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        libglib2.0-0 \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# PyTorch CPU wheels are fetched from the official index to avoid the huge CUDA bundle
COPY requirements.txt .
RUN pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt

# Copy project source
COPY . .

EXPOSE 8000

# Collect static, run migrations, then start the dev server
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
