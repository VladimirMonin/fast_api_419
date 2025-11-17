"""
Модуль настройки аутентификации приложения.

Этот модуль определяет механизмы аутентификации пользователей через JWT токены.
Использует библиотеку fastapi-users для реализации системы аутентификации.

Основные компоненты:
    - Bearer транспорт для передачи токенов в HTTP заголовках
    - JWT стратегия для создания и проверки токенов
    - Backend аутентификации, объединяющий транспорт и стратегию

Пример использования:
    В main.py этот backend используется для создания роутов аутентификации:

    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/auth",
        tags=["auth"]
    )
"""

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from core.config import settings

# Секретный ключ для подписи JWT токенов
# Берётся из конфигурации приложения
SECRET = settings.SECRET_KEY

# Bearer транспорт - определяет, как токен передаётся между клиентом и сервером
# tokenUrl указывает endpoint для получения токена (используется в Swagger UI)
bearer_transport = BearerTransport(tokenUrl="/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """
    Создаёт и возвращает стратегию JWT для аутентификации.

    JWT (JSON Web Token) - это компактный токен, содержащий закодированную информацию
    о пользователе. Токен подписывается секретным ключом, что гарантирует его подлинность.

    Returns:
        JWTStrategy: Стратегия JWT с настроенным секретным ключом и временем жизни токена

    Параметры стратегии:
        secret: Секретный ключ для подписи и проверки токенов
        lifetime_seconds: Время жизни токена в секундах (3600 = 1 час)

    Примечание:
        После истечения времени жизни токен становится недействительным,
        и пользователю нужно будет войти заново.
    """
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


# Backend аутентификации - главный объект, объединяющий транспорт и стратегию
# Используется FastAPI Users для создания endpoints аутентификации
auth_backend = AuthenticationBackend(
    name="jwt",  # Имя backend'а (может быть несколько разных методов аутентификации)
    transport=bearer_transport,  # Как токен передаётся (Bearer в заголовке Authorization)
    get_strategy=get_jwt_strategy,  # Как токен создаётся и проверяется (JWT)
)
