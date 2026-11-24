from app.tasks.celery_app import celery_app
from app.core.logging import logger


@celery_app.task(name="tasks.dummy_ping")
def ping():
    logger.info("Celery worker ping received")
    return "pong"

