import logging
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=BASE_DIR / ".env.dev", override=True)

DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL",
                              "amqp://guest:guest@localhost:5672//")
if not CELERY_BROKER_URL:
    logger = logging.getLogger(__name__)
    logger.error('Configuration Error Occurred: CELERY_BROKER_URL not set')
    raise ValueError("CELERY_BROKER_URL is not set")

CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "django-db")
if not CELERY_RESULT_BACKEND:
    logger = logging.getLogger(__name__)
    logger.error('Configuration Error Occurred: CELERY_RESULT_BACKEND not set')
    raise ValueError("CELERY_RESULT_BACKEND is not set")

# S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_REGION_NAME = os.getenv("S3_REGION_NAME", "")
SAVING_MODE = os.getenv("SAVING_MODE", "local")
