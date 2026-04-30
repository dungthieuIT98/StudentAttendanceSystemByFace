from .base import *  # noqa: F403
from .base import _env  # _env starts with _ so not exported by *


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

