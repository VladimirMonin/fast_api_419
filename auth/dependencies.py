"""
Модуль зависимостей для аутентификации через cookies.

Этот модуль предоставляет функции для извлечения и проверки пользователя
из JWT токена, хранящегося в cookies браузера.

Основные компоненты:
    - get_current_user_from_cookie: Извлекает пользователя из cookie токена

Использование:
    В роутах этот модуль позволяет получать текущего пользователя без
    необходимости передавать токен в заголовках Authorization.
"""

from typing import Optional

import jwt
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db_session
from models.user import User


async def get_current_user_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Извлекает текущего пользователя из JWT токена в cookies.

    Функция выполняет следующие шаги:
    1. Извлекает токен из cookie "access_token"
    2. Если токена нет -> возвращает None
    3. Если токен есть -> декодирует JWT
    4. Извлекает user_id из payload токена
    5. Находит пользователя в БД
    6. Возвращает объект User или None

    Args:
        request: FastAPI Request объект для доступа к cookies
        session: Асинхронная сессия БД (внедряется автоматически)

    Returns:
        Optional[User]: Объект пользователя если токен валиден, иначе None

    Пример использования:
        @router.get("/protected")
        async def protected_route(
            user: User = Depends(get_current_user_from_cookie)
        ):
            if not user:
                return RedirectResponse("/auth/login")
            return {"message": f"Hello, {user.email}"}

    Примечание:
        Функция не выбрасывает исключения при невалидном токене,
        а возвращает None. Это позволяет использовать её для
        публичных страниц, где пользователь опционален.
    """
    # Получаем токен из cookies
    token = request.cookies.get("access_token")

    # Если токена нет, возвращаем None (пользователь не авторизован)
    if not token:
        return None

    try:
        # Декодируем JWT токен
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        # Извлекаем user_id из payload
        user_id: int = payload.get("sub")

        if user_id is None:
            return None

        # Находим пользователя в БД
        result = await session.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        return user

    except jwt.PyJWTError:
        # Если токен невалиден (истёк срок действия, неверная подпись и т.д.)
        return None
    except Exception:
        # Любые другие ошибки (например, проблемы с БД)
        return None
