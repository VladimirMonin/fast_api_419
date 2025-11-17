import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_users import FastAPIUsers

from auth.backend import auth_backend
from auth.manager import get_user_manager
from core.logging_config import setup_logging
from models.user import User
from routes import categories, products, tags
from schemas.user import UserCreate, UserRead, UserUpdate

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

# --- FastAPI Users (Auth) ---
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
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

logger.info("✅ Все роутеры успешно подключены (включая Auth)")
