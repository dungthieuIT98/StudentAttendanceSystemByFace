from .base import *  # noqa: F403
from .base import _env, BASE_DIR  # _env starts with _ so not exported by *


DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("POSTGRES_DB", "face_attendance"),  # noqa: F405
        "USER": _env("POSTGRES_USER", "postgres"),  # noqa: F405
        "PASSWORD": _env("POSTGRES_PASSWORD", "postgres"),  # noqa: F405
        "HOST": _env("POSTGRES_HOST", "db"),  # noqa: F405
        "PORT": int(_env("POSTGRES_PORT", "5432")),  # noqa: F405
    }
}

# Static files configuration for Docker
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# Security settings (commented out for development, uncomment for production)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'

