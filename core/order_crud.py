# core/order_crud.py
"""
CRUD операции для заказов с транзакционной логикой.
Критически важно: создание заказа копирует цены из товаров в OrderItem (слепок данных).
"""

import logging
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.cart_crud import clear_cart, get_cart_with_items
from models.commerce import Order, OrderItem
from schemas.commerce import OrderCreate

logger = logging.getLogger(__name__)


async def create_order(
    session: AsyncSession, user_id: int, order_data: OrderCreate
) -> Order:
    """
    Создать заказ из текущей корзины пользователя.

    ТРАНЗАКЦИОННАЯ ЛОГИКА (явная через async with session.begin()):
    1. Проверяем, что корзина не пуста
    2. Считаем итоговую сумму
    3. Создаем запись Order
    4. Итерируемся по корзине и создаем OrderItem с КОПИРОВАНИЕМ цены и названия (frozen_price, frozen_name)
    5. Очищаем корзину
    6. Коммитим всё в одной транзакции (автоматически при выходе из блока)

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        order_data: Данные заказа (адрес, телефон)

    Returns:
        Order: Созданный заказ со всеми позициями

    Raises:
        ValueError: Если корзина пуста или не найдена
    """
    # Шаг 1: Получаем корзину с товарами (вне транзакции - только чтение)
    cart = await get_cart_with_items(session, user_id)

    if cart is None or len(cart.items) == 0:
        logger.warning(f"⚠️ Попытка создать заказ с пустой корзиной (user_id={user_id})")
        raise ValueError("Корзина пуста. Невозможно создать заказ.")

    logger.info(
        f"📦 Создание заказа для пользователя {user_id}. Товаров в корзине: {len(cart.items)}"
    )

    # Шаг 2: Считаем итоговую сумму (фиксируем на момент создания)
    # Примечание: total_amount - это фиксированное поле в БД (snapshot), а не computed property.
    # Это правильный паттерн для e-commerce: сохраняем сумму "как было", даже если цены изменятся.
    total_amount = sum(
        item.product.price_shmeckles * item.quantity for item in cart.items
    )

    # Шаг 3: Создаем запись заказа
    order = Order(
        user_id=user_id,
        created_at=datetime.utcnow(),
        status="pending",
        total_amount=total_amount,
        delivery_address=order_data.delivery_address,
        phone=order_data.phone,
    )
    session.add(order)
    # Делаем flush, чтобы получить order.id для использования в OrderItem
    await session.flush()

    logger.info(f"✅ Создан заказ #{order.id} на сумму {total_amount} шмеклей")

    # Шаг 4: Создаем позиции заказа с ЗАМОРОЖЕННЫМИ данными
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            # === КРИТИЧЕСКИ ВАЖНО: Копируем данные на момент покупки ===
            frozen_name=cart_item.product.name,
            frozen_price=cart_item.product.price_shmeckles,
        )
        session.add(order_item)

        logger.info(
            f"  📋 Добавлена позиция: {order_item.frozen_name} "
            f"x{order_item.quantity} по {order_item.frozen_price} шмеклей"
        )

    # Шаг 5: Очищаем корзину БЕЗ auto_commit (commit сделает get_db_session)
    await clear_cart(session, user_id, auto_commit=False)

    # Шаг 6: Транзакция автоматически закоммитится в get_db_session()
    # Если произойдет ошибка - автоматический rollback

    # Перезагружаем заказ с позициями для возврата (eager loading)
    # Выполняется ВНЕ транзакции, т.к. это только чтение
    stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    result = await session.execute(stmt)
    order = result.scalar_one()

    logger.info(f"🎉 Заказ #{order.id} успешно создан и корзина очищена")

    return order


async def get_user_orders(session: AsyncSession, user_id: int) -> List[Order]:
    """
    Получить все заказы пользователя (сортировка по дате создания, новые сверху).

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя

    Returns:
        List[Order]: Список заказов с позициями
    """
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    orders = result.scalars().all()

    logger.info(f"📜 Получено {len(orders)} заказов для пользователя {user_id}")

    return list(orders)


async def get_order_by_id(
    session: AsyncSession, user_id: int, order_id: int
) -> Order | None:
    """
    Получить детали конкретного заказа с проверкой доступа.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя (для проверки доступа)
        order_id: ID заказа

    Returns:
        Order | None: Заказ с позициями или None если не найден/недоступен
    """
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if order:
        logger.info(f"🔍 Найден заказ #{order_id} для пользователя {user_id}")
    else:
        logger.warning(
            f"⚠️ Заказ #{order_id} не найден или недоступен для пользователя {user_id}"
        )

    return order
