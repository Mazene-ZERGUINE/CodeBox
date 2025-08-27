from celery import shared_task


@shared_task(name="health.ping", ignore_result=False)
def health_ping():
    return "pong"
