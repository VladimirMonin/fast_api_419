# tasks/notifications.py

import time
from tasks.celery_app import celery_app


@celery_app.task
def send_tg_notification(product_name: str, product_id: int):
    """
    Имитирует отправку уведомления в Telegram.
    """
    message = f"""
**Новый товар в магазине!**
**Название:** {product_name}
**ID:** {product_id}

Подробнее: http://localhost:8000/products/{product_id}
"""
    print("Отправка уведомления в Telegram...")
    time.sleep(5)  # Имитируем задержку на отправку
    print("Уведомление отправлено!")
    return {"status": "success", "message": message}
