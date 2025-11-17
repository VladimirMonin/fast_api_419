from typing import Any, ClassVar, Dict, Tuple

from fastapi_users import schemas
from pydantic import ConfigDict, model_validator


class UserRead(schemas.BaseUser[int]):
    """Схема для чтения данных пользователя (без пароля)."""

    pass


class UserCreate(schemas.BaseUserCreate):
    """Схема для регистрации нового пользователя без критичных флагов."""

    model_config = ConfigDict(extra="forbid")

    _admin_flags: ClassVar[Tuple[str, ...]] = (
        "is_active",
        "is_superuser",
        "is_verified",
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_admin_flags(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = [field for field in cls._admin_flags if field in data]
            if forbidden:
                fields = ", ".join(sorted(forbidden))
                raise ValueError(
                    f"Недопустимые поля в регистрации: {fields}. Управляющие флаги задаются только на сервере."
                )
        return data

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema: Dict[str, Any] = super().__get_pydantic_json_schema__(
            core_schema, handler
        )
        properties = schema.get("properties", {})
        for field in cls._admin_flags:
            properties.pop(field, None)
        required = schema.get("required")
        if isinstance(required, list):
            schema["required"] = [
                item for item in required if item not in cls._admin_flags
            ]
        return schema


class UserUpdate(schemas.BaseUserUpdate):
    """Схема для обновления данных пользователя."""

    pass
