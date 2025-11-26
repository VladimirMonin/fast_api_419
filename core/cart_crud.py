# core/cart_crud.py
"""
CRUD операции для корзины с умной логикой добавления товаров (UPSERT).
UPSERT означает:
- Если товар уже есть в корзине, увеличиваем его количество (UPDATE)
- Если товара нет, создаем новую запись (INSERT)

"""

import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.commerce import Cart, CartItem
from models.product import Product
from schemas.commerce import CartItemCreate

logger = logging.getLogger(__name__)


async def get_or_create_cart(
    session: AsyncSession, user_id: int, auto_commit: bool = True
) -> Cart:
    """
    Получить корзину пользователя или создать новую, если её нет.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        auto_commit: Автоматически делать commit (по умолчанию True)

    Returns:
        Cart: Корзина пользователя
    """
    # Пытаемся найти существующую корзину
    stmt = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()

    if cart is None:
        # Создаем новую корзину
        cart = Cart(user_id=user_id)
        session.add(cart)

        if auto_commit:
            await session.commit()
            await session.refresh(cart)
        else:
            await session.flush()
            await session.refresh(cart)

        logger.info(f"🛒 Создана новая корзина для пользователя {user_id}")
    else:
        logger.info(
            f"🛒 Найдена существующая корзина {cart.id} для пользователя {user_id}"
        )

    return cart


async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int = 1,
    auto_commit: bool = True,
) -> CartItem:
    """
    Добавить товар в корзину с UPSERT логикой.
    - Если товар уже в корзине -> увеличиваем количество
    - Если товара нет -> создаем новую запись

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        product_id: ID товара
        quantity: Количество для добавления (по умолчанию 1)
        auto_commit: Автоматически делать commit (по умолчанию True)

    Returns:
        CartItem: Созданная или обновленная позиция корзины

    Raises:
        ValueError: Если товар с указанным ID не найден
    """
    # Проверяем существование товара
    product_stmt = select(Product).where(Product.id == product_id)
    product_result = await session.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if product is None:
        raise ValueError(f"Товар с ID {product_id} не найден")

    # Получаем или создаем корзину (БЕЗ auto_commit, т.к. мы сами решаем когда коммитить)
    cart = await get_or_create_cart(session, user_id, auto_commit=False)

    # Проверяем, есть ли уже этот товар в корзине
    stmt = select(CartItem).where(
        CartItem.cart_id == cart.id, CartItem.product_id == product_id
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        # Товар уже есть - увеличиваем количество (UPSERT - UPDATE)
        cart_item.quantity += quantity
        logger.info(
            f"➕ Увеличено количество товара {product_id} в корзине до {cart_item.quantity}"
        )
    else:
        # Товара нет - создаем новую запись (UPSERT - INSERT)
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        session.add(cart_item)
        logger.info(
            f"✨ Добавлен новый товар {product_id} в корзину (количество: {quantity})"
        )

    if auto_commit:
        await session.commit()
        await session.refresh(cart_item)
    else:
        await session.flush()
        await session.refresh(cart_item)

    return cart_item


async def merge_cart(
    session: AsyncSession, user_id: int, items: List[CartItemCreate]
) -> None:
    """
    Массовое добавление товаров в корзину (синхронизация гостевой корзины при логине).
    Прогоняет каждый товар через логику add_to_cart.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        items: Список товаров для добавления

    Example:
        items = [
            CartItemCreate(product_id=1, quantity=2),
            CartItemCreate(product_id=5, quantity=1),
        ]
        await merge_cart(session, user_id=42, items=items)
    """
    logger.info(
        f"🔄 Начало синхронизации корзины для пользователя {user_id}. Товаров: {len(items)}"
    )

    for item in items:
        try:
            await add_to_cart(
                session,
                user_id=user_id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
        except ValueError as e:
            # Если товар не найден, пропускаем его и продолжаем
            logger.warning(f"⚠️ Пропущен товар при синхронизации: {e}")
            continue

    logger.info(f"✅ Синхронизация корзины завершена для пользователя {user_id}")


async def get_cart_with_items(session: AsyncSession, user_id: int) -> Cart | None:
    """
    Получить корзину пользователя со всеми товарами (eager loading).

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя

    Returns:
        Cart | None: Корзина со вложенными CartItem и Product, или None если корзины нет
    """
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()

    return cart


async def update_cart_item_quantity(
    session: AsyncSession,
    user_id: int,
    item_id: int,
    quantity: int,
    auto_commit: bool = True,
) -> CartItem:
    """
    Обновить количество товара в корзине.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя (для проверки доступа)
        item_id: ID позиции в корзине
        quantity: Новое количество
        auto_commit: Автоматически делать commit (по умолчанию True)

    Returns:
        CartItem: Обновленная позиция

    Raises:
        ValueError: Если позиция не найдена или пользователь не имеет к ней доступа
    """
    # Получаем позицию с проверкой владельца
    stmt = (
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise ValueError(f"Позиция корзины {item_id} не найдена или недоступна")

    cart_item.quantity = quantity

    if auto_commit:
        await session.commit()
        await session.refresh(cart_item)
    else:
        await session.flush()
        await session.refresh(cart_item)

    logger.info(f"🔄 Обновлено количество позиции {item_id} до {quantity}")

    return cart_item


async def remove_cart_item(
    session: AsyncSession, user_id: int, item_id: int, auto_commit: bool = True
) -> None:
    """
    Удалить позицию из корзины.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя (для проверки доступа)
        item_id: ID позиции для удаления
        auto_commit: Автоматически делать commit (по умолчанию True)

    Raises:
        ValueError: Если позиция не найдена или пользователь не имеет к ней доступа
    """
    # Получаем позицию с проверкой владельца
    stmt = (
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise ValueError(f"Позиция корзины {item_id} не найдена или недоступна")

    await session.delete(cart_item)

    if auto_commit:
        await session.commit()

    logger.info(f"🗑️ Удалена позиция {item_id} из корзины пользователя {user_id}")


async def clear_cart(
    session: AsyncSession, user_id: int, auto_commit: bool = True
) -> None:
    """
    Полностью очистить корзину пользователя.

    Args:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        auto_commit: Автоматически делать commit (по умолчанию True)
    """
    cart = await get_or_create_cart(session, user_id, auto_commit=False)

    # Удаляем все позиции
    stmt = select(CartItem).where(CartItem.cart_id == cart.id)
    result = await session.execute(stmt)
    items = result.scalars().all()

    for item in items:
        await session.delete(item)

    if auto_commit:
        await session.commit()

    logger.info(f"🧹 Корзина пользователя {user_id} полностью очищена")
