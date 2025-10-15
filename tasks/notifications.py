# tasks/notifications.py

import time
from tasks.celery_app import celery_app


@celery_app.task(
    bind=True, max_retries=3, name="tasks.notifications.send_tg_notification"
)
def send_tg_notification(self, product_name: str, product_id: int):
    """
    Имитирует отправку уведомления в Telegram.

    Args:
        product_name: Название товара
        product_id: ID товара

    Returns:
        dict: Статус отправки и текст сообщения
    """
    try:
        message = f"""
**Новый товар в магазине!**
**Название:** {product_name}
**ID:** {product_id}

Подробнее: http://localhost:8000/products/{product_id}
"""
        print(f"[Celery Task] Отправка уведомления в Telegram...")
        print(f"[Celery Task] Товар: {product_name} (ID: {product_id})")
        time.sleep(30)  # Имитируем задержку на отправку
        print(f"[Celery Task] Уведомление успешно отправлено!")
        return {"status": "success", "message": message}
    except Exception as exc:
        print(f"[Celery Task] Ошибка при отправке уведомления: {exc}")
        # Повторная попытка через 5 секунд
        raise self.retry(exc=exc, countdown=5)
