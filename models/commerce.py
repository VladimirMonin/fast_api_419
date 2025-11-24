# models/commerce.py
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.product import Product


class Cart(Base):
    """Корзина пользователя. One-to-One с User."""

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Связь с позициями корзины
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart",
        lazy="raise_on_sql",
        cascade="all, delete-orphan",  # При удалении корзины удаляются все позиции
    )


class CartItem(Base):
    """Позиция в корзине. Many-to-One с Cart и Product."""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Связи
    cart: Mapped["Cart"] = relationship(back_populates="items", lazy="raise_on_sql")
    product: Mapped["Product"] = relationship(lazy="raise_on_sql")


class Order(Base):
    """Заказ пользователя."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Время создания заказа
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Статус заказа (можно заменить на Enum)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )

    # Фиксируем итоговую сумму на момент создания заказа
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Данные доставки
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Связь с позициями заказа
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order",
        lazy="raise_on_sql",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    """
    Позиция заказа - СЛЕПОК товара на момент покупки.
    Сохраняем цену и название, чтобы история не менялась при изменении каталога.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    # product_id может остаться для связи, но данные берем из frozen полей
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # === КРИТИЧЕСКИ ВАЖНО: Замороженные данные ===
    # Копируем название и цену из Product на момент создания заказа
    frozen_name: Mapped[str] = mapped_column(String(100), nullable=False)
    frozen_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Связи
    order: Mapped["Order"] = relationship(back_populates="items", lazy="raise_on_sql")
