# core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings

import asyncio

# Импортируем модели для регистрации в Base.metadata
from models.base import Base  # Импортируем Base из пакета models
from models.product import Product  # noqa: F401

# URL для подключения к асинхронной SQLite
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

# Стартовая инициализация базы данных
# ВАЖНО. Оно не отслеживает изменения моделей автоматически. Это просто стартер. Он не изменит ваши таблицы при изменении моделей. Создаст таблицу если её нет. Если есть - пропустит.


async def init_db():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
