# utils/telegram.py
import logging
import telegram
from config import settings

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
