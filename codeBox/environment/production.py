import logging
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load production env file at repo root (do NOT commit real secrets)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


DEBUG = False
ALLOWED_HOSTS = _csv("ALLOWED_HOSTS")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production.")

# Database configuration
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.postgresql")
if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", ""),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "django-db")

if not CELERY_BROKER_URL:
    logger = logging.getLogger(__name__)
    logger.error('Configuration Error Occurred: CELERY_BROKER_URL not set')
    raise ValueError("CELERY_BROKER_URL is not set")

if not CELERY_RESULT_BACKEND:
    logger = logging.getLogger(__name__)
    logger.error('Configuration Error Occurred: CELERY_RESULT_BACKEND not set')
    raise ValueError("CELERY_RESULT_BACKEND is not set")

# Local vs cloud saving strategy toggle
SAVING_MODE = os.getenv("SAVING_MODE", "local")  # "local" or "s3"

# S3 buckets configurations
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_REGION_NAME = os.getenv("S3_REGION_NAME", "")
