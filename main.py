import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes import products, categories, tags
from core.logging_config import setup_logging

# Настройка логирования при импорте модуля
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 Запуск приложения FastAPI")
    logger.info("📋 Регистрация роутеров: categories, tags, products")
    yield
    logger.info("🛑 Остановка приложения FastAPI")


# --- Приложение FastAPI ---
app = FastAPI(
    title="Учебное приложение Python419",
    description="Пример простого API для управления пользователями",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router, prefix="/categories", tags=["Категории"])
app.include_router(tags.router, prefix="/tags", tags=["Теги"])
app.include_router(products.router, prefix="/products", tags=["Товары"])

logger.info("✅ Все роутеры успешно подключены")
