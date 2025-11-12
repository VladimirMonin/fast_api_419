import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# --- Настройка CORS для React фронтенда ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (React)
        "http://localhost:3000",  # Create React App dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,  # Разрешить отправку куки и авторизационных заголовков
    allow_methods=["*"],  # Разрешить все HTTP методы (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)

app.include_router(
    categories.router, prefix="/categories", tags=["Категории"]
)  # "/{category_id}",
app.include_router(tags.router, prefix="/tags", tags=["Теги"])
app.include_router(products.router, prefix="/products", tags=["Товары"])

# Раздача статических файлов (загруженные изображения)
# "/uploads" - маршрут для доступа к загруженным файлам
# directory="uploads" - папка на сервере, где хранятся файлы
# name - имя монтируемого приложения - оно может использоваться для обратного вызова URL
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

logger.info("✅ Все роутеры успешно подключены")
