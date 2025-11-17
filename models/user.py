from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    """Модель пользователя fastapi-users."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Дополнительные поля можно добавить при необходимости, например:
    # first_name: Mapped[str | None]

    # Связи, например с корзиной, появятся позже:
    # cart = relationship("Cart", uselist=False, back_populates="user")
