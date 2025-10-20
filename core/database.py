# core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings

# URL для подключения к асинхронной SQLite
# Три слеша означают относительный путь, четыре — абсолютный
# DATABASE_URL = "sqlite+aiosqlite:///./test.db"
DATABASE_URL = settings.DATABASE_URL


# Cоздание асинхронного движка базы данных
#  echo=True — включает логирование SQL-запросов в консоль
engine = create_async_engine(DATABASE_URL, echo=True)

# Создание фабрики асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    # bind - это движок, с которым будут работать сессии
    # expire_on_commit=False - отключает автоматическое обновление объектов после коммита
    bind=engine,
    expire_on_commit=False,
)
