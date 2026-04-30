from .base import *  # noqa: F403
from .base import _env, BASE_DIR  # not exported by * (start with _ or shadow builtins)

DEBUG = True
ALLOWED_HOSTS = ["*"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}


# If Postgres env vars are present, prefer Postgres even in local.
_pg_db = _env("POSTGRES_DB")  # noqa: F405
_pg_user = _env("POSTGRES_USER")  # noqa: F405
_pg_password = _env("POSTGRES_PASSWORD")  # noqa: F405
_pg_host = _env("POSTGRES_HOST")  # noqa: F405
_pg_port = _env("POSTGRES_PORT")  # noqa: F405

if all([_pg_db, _pg_user, _pg_password, _pg_host, _pg_port]):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _pg_db,
            "USER": _pg_user,
            "PASSWORD": _pg_password,
            "HOST": _pg_host,
            "PORT": int(_pg_port),
        }
    }

