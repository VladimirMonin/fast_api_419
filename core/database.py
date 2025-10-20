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
        # Для чистоты эксперимента будем удалять таблицы и пересоздавать их
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # ВСЕ ЭКСПЕРИМЕНТЫ ТУТ В ФОРМАТЕ СКРИПТА!!!!!!
        async with AsyncSessionLocal() as session:
            product_1 = Product(
                name="Коробка с Мисиксами",
                description="Нужна помощь по дому? Нажмите кнопку, и появится Мисикс, готовый выполнить одно ваше поручение. Существование для него — боль, так что не затягивайте!",
                image_url="/images/meeseeks-box.webp",
                price_shmeckles=19.99,
                price_flurbos=9.8,
            )

            product_2 = Product(
                name="Портальная пушка (б/у)",
                description="легка поцарапана, заряд портальной жидкости на 37%. Возврату не подлежит. Может пахнуть приключениями и чужими измерениями. Осторожно: привлекает внимание Цитадели.",
                image_url="/images/portal-gun.webp",
                price_shmeckles=9999.99,
                price_flurbos=4999.99,
            )

            # session.add - добавит 1 позицию
            # session.add_all - добавит пачку объектов
            session.add_all([product_1, product_2])
            await session.commit()

        # Выборка по ID - новый контекст для сессии (потому что предыдущий был закрыт commit-ом)
        async with AsyncSessionLocal() as session:
            result = await session.get(Product, 2)
            print(f"Product ID 1: {result.name}, Price: {result.price_shmeckles} шмекелей")

            # Обновление объекта
            result.name = "Портальная пушка (как новая)"
            await session.commit()

        # Удаление по ID - новый контекст для сессии
        async with AsyncSessionLocal() as session:
            result = await session.get(Product, 1)
            await session.delete(result)
            await session.commit()



if __name__ == "__main__":
    asyncio.run(init_db())
