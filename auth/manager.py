"""
Модуль управления пользователями (User Manager).

Этот модуль содержит бизнес-логику для управления пользователями:
регистрация, сброс пароля, верификация email и другие операции.

Основные компоненты:
    - UserManager: Класс с логикой управления пользователями
    - get_user_manager: Dependency для получения экземпляра UserManager

Возможности UserManager:
    - Регистрация новых пользователей
    - Сброс пароля через email
    - Верификация email адресов
    - Обработка событий (например, после регистрации)

Связь с другими модулями:
    - Использует auth.database для доступа к БД
    - Использует models.user.User как модель пользователя
    - Использует core.config для секретных ключей
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from auth.database import get_user_db
from core.config import settings
from models.user import User

# Секретный ключ для подписи токенов сброса пароля и верификации
SECRET = settings.SECRET_KEY


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Менеджер для управления пользователями приложения.

    Этот класс наследуется от BaseUserManager и добавляет поддержку
    целочисленных ID через IntegerIDMixin.

    Attributes:
        reset_password_token_secret: Секретный ключ для токенов сброса пароля
        verification_token_secret: Секретный ключ для токенов верификации email

    Основные методы (унаследованные от BaseUserManager):
        - create(): Создание нового пользователя
        - get(): Получение пользователя по ID
        - get_by_email(): Получение пользователя по email
        - authenticate(): Проверка учётных данных
        - update(): Обновление данных пользователя
        - delete(): Удаление пользователя
        - request_verify(): Запрос верификации email
        - verify(): Верификация email по токену
        - forgot_password(): Запрос сброса пароля
        - reset_password(): Сброс пароля по токену

    Примечание:
        Этот класс можно расширять, добавляя свои методы или переопределяя
        существующие для кастомной логики.
    """

    # Секретные ключи для подписи токенов
    # Используются для безопасной генерации временных токенов
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        """
        Callback-метод, вызываемый после успешной регистрации пользователя.

        Этот метод можно переопределить для выполнения дополнительных действий
        после регистрации пользователя, например:
        - Отправка приветственного email
        - Логирование события регистрации
        - Отправка уведомления в Telegram
        - Создание связанных записей в БД
        - Начисление бонусов новому пользователю

        Args:
            user: Только что зарегистрированный пользователь
            request: HTTP request объект (может быть None, если регистрация
                    происходит не через HTTP endpoint)

        Пример расширения:
            async def on_after_register(self, user: User, request: Optional[Request] = None):
                print(f"User {user.id} has registered.")
                # Отправка email
                await send_welcome_email(user.email)
                # Уведомление в Telegram
                await notify_admin_new_user(user.email)
        """
        print(f"User {user.id} has registered.")


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """
    Dependency для получения экземпляра UserManager.

    Эта функция создаёт и предоставляет UserManager для использования
    в FastAPI endpoints. UserManager содержит всю бизнес-логику для
    работы с пользователями.

    Args:
        user_db: База данных пользователей, автоматически внедряется через Depends

    Yields:
        UserManager: Менеджер пользователей, готовый к использованию

    Пример использования:
        @app.post("/register")
        async def register(
            user_manager: UserManager = Depends(get_user_manager)
        ):
            # Здесь можно использовать user_manager для операций с пользователями
            new_user = await user_manager.create(user_data)
            return new_user

    Примечание:
        Используется FastAPI Users для автоматической генерации
        endpoints регистрации, логина и других операций.
    """
    yield UserManager(user_db)
