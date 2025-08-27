import logging
from kombu import Connection
from celery.result import AsyncResult
from celery.exceptions import TimeoutError

logger = logging.getLogger(__name__)


def check_broker(broker_url: str, timeout: int = 5) -> None:
    conn = Connection(broker_url, connect_timeout=timeout,
                      transport_options={"connect_timeout": timeout})
    conn.ensure_connection(max_retries=0)
    conn.release()


def check_workers(app, timeout: int = 5) -> None:
    replies = app.control.ping(timeout=timeout)
    if not replies:
        raise RuntimeError(
            "No Celery workers replied to ping (is the worker running?).")


def check_backend(app, timeout: int = 5) -> None:
    try:
        res: AsyncResult = app.send_task("health.ping")
        value = res.get(timeout=timeout)
        if value != "pong":
            raise RuntimeError(f"Unexpected healthcheck result: {value}")
    except TimeoutError as e:
        raise RuntimeError(
            "Result backend timeout (is the backend configured and reachable?)") from e
