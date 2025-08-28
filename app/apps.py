import logging

from django.apps import AppConfig
from django.conf import settings
from .services.paths_service import ensure_storage_dir

logger = logging.getLogger(__name__)


class CodeBoxAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        logger.info("Setting up files storage ...")
        ensure_storage_dir(getattr(settings, "STORAGE_IN"), "STORAGE_IN")
        ensure_storage_dir(getattr(settings, "STORAGE_OUT"), "STORAGE_OUT")
        logger.info("Files storage setup complete.")
