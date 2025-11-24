# schemas/commerce.py
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, computed_field


# === СХЕМЫ ДЛЯ КОРЗИНЫ ===


class CartItemCreate(BaseModel):
    """
    Схема для добавления товара в корзину.

    Используется в:
    - POST /cart/items - добавить товар в корзину
    - POST /cart/merge - массовая синхронизация (список таких объектов)
    """

    product_id: int = Field(
        ..., description="ID товара для добавления в корзину", example=1, gt=0
    )
    quantity: int = Field(default=1, description="Количество товара", example=2, ge=1)


class CartItemUpdate(BaseModel):
    """
    Схема для изменения количества товара в корзине (кнопки +/-).

    Используется в:
    - PATCH /cart/items/{id} - обновить количество конкретной позиции
    """

    quantity: int = Field(..., description="Новое количество товара", example=3, ge=1)


class ProductInCart(BaseModel):
    """
    Вложенная схема товара для отображения в корзине.

    Содержит только необходимые поля товара (без описания и категории).
    Автоматически включается в CartItemRead через relationship.
    НЕ используется напрямую в эндпоинтах - только как часть CartItemRead.
    """

    id: int = Field(..., description="ID товара")
    name: str = Field(..., description="Название товара")
    price_shmeckles: float = Field(..., description="Цена в шмеклях")
    price_flurbos: float = Field(..., description="Цена в флурбо")
    image_url: str | None = Field(None, description="URL изображения")

    model_config = ConfigDict(from_attributes=True)


class CartItemRead(BaseModel):
    """
    Схема для отображения одной позиции в корзине.

    Содержит quantity + вложенный объект Product с актуальными ценами.
    Автоматически включается в CartRead как список items.
    НЕ используется напрямую в эндпоинтах - только как часть CartRead.
    """

    id: int = Field(..., description="ID позиции в корзине")
    product_id: int = Field(..., description="ID товара")
    quantity: int = Field(..., description="Количество")
    product: ProductInCart = Field(..., description="Данные товара")

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    """
    Схема для отображения полной корзины пользователя.

    Содержит:
    - Список позиций (CartItemRead) с вложенными товарами
    - Автоматически вычисляемое поле total_price (сумма корзины в шмеклях)

    Используется в:
    - GET /cart - получить текущую корзину со всеми товарами
    """

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
    """
    Схема для массового добавления товаров в корзину (синхронизация гостевой корзины).

    Используется когда пользователь входит в систему и нужно слить его локальную
    корзину из браузера с серверной корзиной.

    Используется в:
    - POST /cart/merge - синхронизировать гостевую корзину при логине

    Принимает список CartItemCreate объектов.
    """

    items: List[CartItemCreate] = Field(
        ..., description="Список товаров для добавления в корзину"
    )


# === СХЕМЫ ДЛЯ ЗАКАЗОВ ===


class OrderCreate(BaseModel):
    """
    Схема для создания заказа из текущей корзины.

    ВАЖНО: Товары НЕ передаются! Они автоматически берутся из корзины пользователя.
    После создания заказа корзина очищается.

    Используется в:
    - POST /orders - создать заказ из корзины
    """

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
    """
    Схема для отображения одной позиции заказа с ЗАМОРОЖЕННЫМИ данными.

    КРИТИЧЕСКИ ВАЖНО:
    - frozen_name и frozen_price - это СЛЕПОК данных на момент покупки
    - Даже если товар изменится/удалится, история заказа останется неизменной

    Автоматически включается в OrderRead как список items.
    НЕ используется напрямую в эндпоинтах - только как часть OrderRead.
    """

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
    """
    Схема для отображения полного заказа с историей покупки.

    Содержит:
    - Фиксированную сумму (total_amount) на момент создания
    - Список позиций (OrderItemRead) с замороженными ценами и названиями
    - Адрес доставки и телефон

    Используется в:
    - POST /orders - возврат созданного заказа
    - GET /orders - список всех заказов пользователя
    - GET /orders/{id} - детали конкретного заказа
    """

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
