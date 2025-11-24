# schemas/commerce.py
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, computed_field


# === СХЕМЫ ДЛЯ КОРЗИНЫ ===


class CartItemCreate(BaseModel):
    """Схема для добавления товара в корзину."""

    product_id: int = Field(
        ..., description="ID товара для добавления в корзину", example=1, gt=0
    )
    quantity: int = Field(default=1, description="Количество товара", example=2, ge=1)


class CartItemUpdate(BaseModel):
    """Схема для обновления количества товара в корзине."""

    quantity: int = Field(..., description="Новое количество товара", example=3, ge=1)


class ProductInCart(BaseModel):
    """Упрощенная схема товара для отображения в корзине."""

    id: int = Field(..., description="ID товара")
    name: str = Field(..., description="Название товара")
    price_shmeckles: float = Field(..., description="Цена в шмеклях")
    price_flurbos: float = Field(..., description="Цена в флурбо")
    image_url: str | None = Field(None, description="URL изображения")

    model_config = ConfigDict(from_attributes=True)


class CartItemRead(BaseModel):
    """Схема для отображения позиции в корзине."""

    id: int = Field(..., description="ID позиции в корзине")
    product_id: int = Field(..., description="ID товара")
    quantity: int = Field(..., description="Количество")
    product: ProductInCart = Field(..., description="Данные товара")

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    """Схема для отображения корзины целиком."""

    id: int = Field(..., description="ID корзины")
    user_id: int = Field(..., description="ID пользователя")
    items: List[CartItemRead] = Field(
        default=[], description="Список товаров в корзине"
    )

    @computed_field
    @property
    def total_price(self) -> float:
        """Вычисляемое поле: общая стоимость корзины в шмеклях."""
        return sum(item.product.price_shmeckles * item.quantity for item in self.items)

    model_config = ConfigDict(from_attributes=True)


# === СХЕМА ДЛЯ СИНХРОНИЗАЦИИ (ГОСТЬ -> ЮЗЕР) ===


class CartItemBatch(BaseModel):
    """Схема для массового добавления товаров (синхронизация гостевой корзины)."""

    items: List[CartItemCreate] = Field(
        ..., description="Список товаров для добавления в корзину"
    )


# === СХЕМЫ ДЛЯ ЗАКАЗОВ ===


class OrderCreate(BaseModel):
    """Схема для создания заказа. Товары берутся из текущей корзины."""

    delivery_address: str = Field(
        ...,
        description="Адрес доставки",
        example="ул. Плутон, д. 42, кв. 137",
        min_length=10,
        max_length=500,
    )
    phone: str = Field(
        ...,
        description="Контактный телефон",
        example="+7 (999) 123-45-67",
        min_length=10,
        max_length=20,
    )


class OrderItemRead(BaseModel):
    """Схема для отображения позиции заказа с замороженными данными."""

    id: int = Field(..., description="ID позиции заказа")
    product_id: int = Field(..., description="ID товара (на момент заказа)")
    quantity: int = Field(..., description="Количество")
    frozen_name: str = Field(
        ..., description="Название товара на момент создания заказа"
    )
    frozen_price: float = Field(
        ..., description="Цена товара на момент создания заказа (в шмеклях)"
    )

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    """Схема для отображения заказа."""

    id: int = Field(..., description="ID заказа")
    user_id: int = Field(..., description="ID пользователя")
    created_at: datetime = Field(..., description="Дата и время создания заказа")
    status: str = Field(..., description="Статус заказа", example="pending")
    total_amount: float = Field(
        ..., description="Итоговая сумма заказа (зафиксирована на момент создания)"
    )
    delivery_address: str = Field(..., description="Адрес доставки")
    phone: str = Field(..., description="Контактный телефон")
    items: List[OrderItemRead] = Field(
        default=[], description="Список товаров в заказе"
    )

    model_config = ConfigDict(from_attributes=True)
