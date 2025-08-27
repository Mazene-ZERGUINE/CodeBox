from django.conf import settings
from codeBox.config.code_box_celery import app
from codeBox.config.celery_health import check_broker, check_workers, check_backend
from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class CodeBoxConfig(AppConfig):
    name = "codeBox"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        try:
            broker_url = app.conf.broker_url
            check_broker(broker_url, timeout=5)
            check_workers(app, timeout=5)

            if getattr(settings, "CELERY_RESULT_BACKEND", None):
                check_backend(app, timeout=5)

            logger.info("Celery healthcheck OK: broker + worker%s ready.",
                        " + backend" if getattr(settings, "CELERY_RESULT_BACKEND",
                                                None) else "")
        except Exception as e:
            logger.critical("Celery healthcheck FAILED: %s", e, exc_info=True)
            raise SystemExit(1)
