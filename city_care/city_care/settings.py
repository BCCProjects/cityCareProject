from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv(BASE_DIR / ".env")


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS") or ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "storages",
    "django_crontab",
    "accounts",
    "core.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "city_care.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "city_care.wsgi.application"
ASGI_APPLICATION = "city_care.asgi.application"

CHANNEL_LAYER_BACKEND = os.getenv("CHANNEL_LAYER_BACKEND", "memory").lower()
CHANNEL_LAYER_REDIS_URL = os.getenv("CHANNEL_LAYER_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")

if CHANNEL_LAYER_BACKEND == "redis":
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [CHANNEL_LAYER_REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DATABASE", "city_care"),
            "USER": os.getenv("MYSQL_USER", "city_care"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD", "city_care"),
            "HOST": os.getenv("MYSQL_HOST", "localhost"),
            "PORT": os.getenv("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("SQLITE_NAME", "db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.Employee"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.api.authentication.CitizenJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

CORS_DEFAULT_ORIGIN = ["http://localhost:3000", "http://localhost:8081", "exp://192.168.1.14:8081"] if DEBUG else ""
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", CORS_DEFAULT_ORIGIN)
CORS_ALLOW_ALL_ORIGINS = False
if not CORS_ALLOWED_ORIGINS and DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + ["x-user", "x-app", "x-signature"]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

# Security headers expected values (env-driven)
# Honor the names defined in .env: X_USER, X_APP, X_SIGNATURE
# Keep backward compatibility with previous API_SECURITY_* names if present.
API_SECURITY_USER = os.getenv("X_USER", os.getenv("API_SECURITY_USER", "local_user"))
API_SECURITY_APP = os.getenv("X_APP", os.getenv("API_SECURITY_APP", "local_app"))
API_SECURITY_SIGNATURE = os.getenv(
    "X_SIGNATURE", os.getenv("API_SECURITY_SIGNATURE", "local_signature")
)

# Supabase S3-compatible storage (used by attachments)
USE_SUPABASE_ATTACHMENTS = os.getenv("SUPABASE_STORAGE_ENABLED", "1") == "1"
AWS_ACCESS_KEY_ID = os.getenv("SUPABASE_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("SUPABASE_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_ATTACHMENT_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = os.getenv("SUPABASE_S3_ENDPOINT_URL", "")
AWS_S3_SIGNATURE_VERSION = os.getenv("SUPABASE_S3_SIGNATURE_VERSION", "s3v4")
AWS_S3_ADDRESSING_STYLE = os.getenv("SUPABASE_S3_ADDRESSING_STYLE", "path")
AWS_S3_REGION_NAME = os.getenv("SUPABASE_S3_REGION", "us-east-1")
AWS_QUERYSTRING_AUTH = False  # do not append signed query params to public URLs

# Attachment key prefix
SUPABASE_ATTACHMENT_PREFIX = os.getenv("SUPABASE_ATTACHMENT_PREFIX", "reportImages")

# For public access via Supabase object API (bucket must be public)
_supabase_project_url = os.getenv("SUPABASE_PROJECT_URL", "").rstrip("/")
if _supabase_project_url and AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = f"{_supabase_project_url.replace('https://', '').replace('http://', '')}/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}"
    AWS_S3_URL_PROTOCOL = "https:"

# Backups (Supabase S3) envs — herda endpoint/keys do SUPABASE_* por padrão
BACKUP_S3_ENDPOINT_URL = os.getenv("SUPABASE_S3_ENDPOINT_URL", AWS_S3_ENDPOINT_URL)
BACKUP_S3_ACCESS_KEY_ID = os.getenv("SUPABASE_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
BACKUP_S3_SECRET_ACCESS_KEY = os.getenv("SUPABASE_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
BACKUP_S3_BUCKET = os.getenv("SUPABASE_BACKUP_BUCKET_NAME", "backupBucket")
BACKUP_S3_REGION = os.getenv("SUPABASE_S3_REGION", AWS_S3_REGION_NAME)
BACKUP_COMPLETE_PREFIX = os.getenv("SUPABASE_BACKUP_COMPLETE_PREFIX", "completeBackup")
BACKUP_DIFFERENTIAL_PREFIX = os.getenv("SUPABASE_BACKUP_DIFFERENTIAL_PREFIX", "differentialBackup")

# Cronjobs
CRONJOBS = [
    # Ignorar relatórios sem atualização há 3 dias (diariamente às 02:00)
    ("0 2 * * *", "django.core.management.call_command", ["mark_reports_ignored", "--hours", "72"]),
    # Backup diferencial diário às 02:20
    ("20 2 * * *", "django.core.management.call_command", ["backup_diff"]),
    # Backup completo semanal (domingo às 03:00)
    ("0 3 * * 0", "django.core.management.call_command", ["backup_full"]),
]
