from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """Схема для чтения данных пользователя (без пароля)."""

    pass


class UserCreate(schemas.BaseUserCreate):
    """Схема для регистрации нового пользователя."""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Схема для обновления данных пользователя."""

    pass
