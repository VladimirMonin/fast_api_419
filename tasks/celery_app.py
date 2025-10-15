# tasks/celery_app.py
from celery import Celery
import celery
from config import settings

celery_app = Celery(
    "tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

celery_app.autodiscover_tasks(["tasks"])
