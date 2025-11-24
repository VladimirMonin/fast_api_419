# routes/cart.py
"""
API эндпоинты для управления корзиной.
Все операции требуют авторизации (Depends(get_current_active_user)).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession

from auth.backend import auth_backend
from auth.manager import get_user_manager
from core.cart_crud import (
    add_to_cart,
    clear_cart,
    get_cart_with_items,
    merge_cart,
    remove_cart_item,
    update_cart_item_quantity,
)
from core.database import get_db_session
from models.user import User
from schemas.commerce import CartItemBatch, CartItemCreate, CartItemUpdate, CartRead

logger = logging.getLogger(__name__)

router = APIRouter()

# === Dependency для получения текущего авторизованного пользователя ===
fastapi_users_instance = FastAPIUsers[User, int](get_user_manager, [auth_backend])

get_current_active_user = fastapi_users_instance.current_user(active=True)


@router.get(
    "/",
    response_model=CartRead,
    summary="Получить текущую корзину",
    description="Возвращает корзину текущего пользователя со всеми товарами и общей суммой",
)
async def get_cart(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Получить корзину текущего пользователя.
    Возвращает пустую корзину, если товаров нет.
    """
    logger.info(f"🛒 Запрос корзины для пользователя {user.id}")

    cart = await get_cart_with_items(session, user.id)

    if cart is None:
        # Возвращаем пустую корзину
        from models.commerce import Cart

        cart = Cart(id=0, user_id=user.id, items=[])
        logger.info(f"📭 Корзина пользователя {user.id} пуста")

    logger.info(
        f"✅ Корзина пользователя {user.id} получена. Товаров: {len(cart.items)}"
    )
    return cart


@router.post(
    "/items",
    response_model=dict,
    summary="Добавить товар в корзину",
    description="Добавляет товар в корзину. Если товар уже есть, увеличивает количество (UPSERT)",
)
async def add_item_to_cart(
    item_data: CartItemCreate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Добавить товар в корзину с UPSERT логикой.
    """
    logger.info(
        f"➕ Добавление товара {item_data.product_id} в корзину пользователя {user.id}"
    )

    try:
        cart_item = await add_to_cart(
            session, user.id, item_data.product_id, item_data.quantity
        )
        logger.info("Товар успешно добавлен в корзину")
        return {
            "message": "Товар добавлен в корзину",
            "cart_item_id": cart_item.id,
            "quantity": cart_item.quantity,
        }
    except ValueError as e:
        logger.error(f"❌ Ошибка добавления товара: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/merge",
    response_model=dict,
    summary="Синхронизировать гостевую корзину",
    description="Массовое добавление товаров (используется при логине для слияния гостевой корзины с пользовательской)",
)
async def merge_guest_cart(
    batch_data: CartItemBatch,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Синхронизация гостевой корзины с пользовательской при логине.
    """
    logger.info(
        f"🔄 Синхронизация корзины для пользователя {user.id}. Товаров: {len(batch_data.items)}"
    )

    await merge_cart(session, user.id, batch_data.items)

    return {
        "message": "Корзина успешно синхронизирована",
        "merged_items": len(batch_data.items),
    }


@router.patch(
    "/items/{item_id}",
    response_model=dict,
    summary="Обновить количество товара",
    description="Изменяет количество товара в корзине (для кнопок +/-)",
)
async def update_item_quantity(
    item_id: int,
    update_data: CartItemUpdate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Обновить количество товара в корзине.
    """
    logger.info(f"🔄 Обновление количества позиции {item_id} до {update_data.quantity}")

    try:
        cart_item = await update_cart_item_quantity(
            session, user.id, item_id, update_data.quantity
        )
        return {
            "message": "Количество обновлено",
            "cart_item_id": cart_item.id,
            "quantity": cart_item.quantity,
        }
    except ValueError as e:
        logger.error(f"❌ Ошибка обновления количества: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/items/{item_id}",
    response_model=dict,
    summary="Удалить товар из корзины",
    description="Удаляет конкретную позицию из корзины",
)
async def delete_cart_item(
    item_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Удалить позицию из корзины.
    """
    logger.info(f"🗑️ Удаление позиции {item_id} из корзины пользователя {user.id}")

    try:
        await remove_cart_item(session, user.id, item_id)
        return {"message": "Товар удален из корзины", "cart_item_id": item_id}
    except ValueError as e:
        logger.error(f"❌ Ошибка удаления позиции: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/",
    response_model=dict,
    summary="Очистить корзину",
    description="Полностью очищает корзину пользователя",
)
async def clear_user_cart(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Полная очистка корзины.
    """
    logger.info(f"🧹 Очистка корзины пользователя {user.id}")

    await clear_cart(session, user.id)

    return {"message": "Корзина очищена"}
