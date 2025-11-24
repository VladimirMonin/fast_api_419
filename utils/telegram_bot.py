# utils/telegram.py
import logging
import telegram
from core.config import settings

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)


async def send_telegram_message(message: str, parse_mode: str = "Markdown"):
    """Отправка сообщения в Telegram через бота"""
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_API_KEY)
        # Имитируем более длительную асинхронную операцию
        await bot.send_message(
            chat_id=settings.TELEGRAM_USER_ID, text=message, parse_mode=parse_mode
        )
        logging.info(
            f'Сообщение "{message}" отправлено в чат {settings.TELEGRAM_USER_ID}'
        )
    except Exception as e:
        logging.error(
            f"Ошибка отправки сообщения в чат {settings.TELEGRAM_USER_ID}: {e}"
        )
        raise
    else:
        logging.debug(f"Сообщение успешно отправлено: {message}")


async def send_order_notification(
    order_id: int, total_amount: float, user_email: str, delivery_address: str
):
    """
    Отправить уведомление о новом заказе в Telegram.

    Args:
        order_id: ID заказа
        total_amount: Сумма заказа
        user_email: Email клиента
        delivery_address: Адрес доставки
    """
    message = (
        f"💰 *Новый заказ #{order_id}!*\n\n"
        f"📊 Сумма: *{total_amount:.2f} шмеклей*\n"
        f"👤 Клиент: `{user_email}`\n"
        f"📍 Адрес: {delivery_address}\n\n"
        f"🎉 Заказ готов к обработке!"
    )

    await send_telegram_message(message, parse_mode="Markdown")
    logging.info(f"📬 Уведомление о заказе #{order_id} отправлено в Telegram")
