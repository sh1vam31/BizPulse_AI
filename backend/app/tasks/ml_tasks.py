from app.tasks.celery_app import celery_app
from app.core.logging import logger


@celery_app.task(name="tasks.ml_ping")
def ml_ping():
    logger.info("Celery ML worker ping received")
    return "ml_pong"

