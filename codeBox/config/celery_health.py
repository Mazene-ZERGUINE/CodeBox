"""
This service provides low-level healthcheck utilities for verifying the
availability and proper functioning of a Celery deployment. It is useful
for monitoring, readiness checks, and diagnosing connectivity issues.

The checks include:

1. **Broker check (`check_broker`)**
   - Verifies that the message broker (RabbitMQ) is reachable.
   - Raises an exception if the broker cannot be reached.

2. **Worker check (`check_workers`)**
   - Sends a `ping` control command to all registered workers.
   - Ensures that at least one worker replies.
   - Raises a `RuntimeError` if no workers respond.

3. **Backend check (`check_backend`)**
   - Sends a lightweight test task (`health.ping`) through Celery.
   - Waits for the result from the result backend within a given timeout.
   - Ensures the backend is properly configured and reachable.
   - Raises a `RuntimeError` if the backend times out or returns
     an unexpected response.

Together, these functions provide a full health validation of:
- The broker (message queue),
- The workers (task executors),
- The result backend (task result store).
"""
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
