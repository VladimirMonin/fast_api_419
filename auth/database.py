"""
Модуль для работы с базой данных пользователей.

Этот модуль предоставляет доступ к таблице пользователей в базе данных
через SQLAlchemy ORM. Использует паттерн Dependency Injection FastAPI
для внедрения database session.

Основные компоненты:
    - get_user_db: Dependency для получения доступа к БД пользователей

Связь с другими модулями:
    - Использует core.database для получения database session
    - Использует models.user.User как модель пользователя
    - Используется в auth.manager для операций с пользователями
"""

from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.user import User


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, int], None]:
    """
    Dependency для получения доступа к базе данных пользователей.

    Эта функция - это FastAPI Dependency, которая:
    1. Получает асинхронную database session через Depends(get_db_session)
    2. Создаёт SQLAlchemyUserDatabase - специальный адаптер для работы с пользователями
    3. Предоставляет его для использования в других функциях

    Args:
        session: Асинхронная сессия SQLAlchemy, автоматически внедряется FastAPI

    Yields:
        SQLAlchemyUserDatabase[User, int]: Объект для работы с таблицей пользователей
            - User: Модель пользователя (SQLAlchemy модель)
            - int: Тип ID пользователя (в нашем случае целое число)

    Пример использования:
        @app.get("/users/me")
        async def get_current_user(
            user_db: SQLAlchemyUserDatabase = Depends(get_user_db)
        ):
            # Здесь можно использовать user_db для запросов к БД
            user = await user_db.get(user_id)
            return user

    Примечание:
        AsyncGenerator используется для корректного управления ресурсами.
        После использования сессия автоматически закрывается.
    """

    yield SQLAlchemyUserDatabase(session, User)
