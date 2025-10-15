# tasks/celery_app.py
from celery import Celery
from config import settings

celery_app = Celery(
    "tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

# Настройки для Windows
celery_app.conf.update(
    worker_concurrency=1,
    task_acks_late=True,
    worker_pool="solo",  # Обязательный параметр для Windows
    broker_connection_retry_on_startup=True,
)

# Импортируем задачи явно, чтобы они зарегистрировались
# Это делается после создания экземпляра celery_app
from tasks import notifications  # noqa: E402
