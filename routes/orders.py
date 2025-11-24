# routes/orders.py
"""
API эндпоинты для работы с заказами.
Все операции требуют авторизации.
"""

import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession

from auth.backend import auth_backend
from auth.manager import get_user_manager
from core.database import get_db_session
from core.order_crud import create_order, get_order_by_id, get_user_orders
from models.user import User
from schemas.commerce import OrderCreate, OrderRead
from utils.telegram_bot import send_order_notification

logger = logging.getLogger(__name__)

router = APIRouter()

# === Dependency для получения текущего авторизованного пользователя ===
fastapi_users_instance = FastAPIUsers[User, int](get_user_manager, [auth_backend])
get_current_active_user = fastapi_users_instance.current_user(active=True)


@router.post(
    "/",
    response_model=OrderRead,
    summary="Создать заказ",
    description="Создает заказ из текущей корзины пользователя. Корзина очищается после создания заказа.",
)
async def create_new_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Создать заказ из корзины.
    Товары берутся из текущей корзины, цены фиксируются (frozen_price).
    После создания заказа корзина автоматически очищается.
    Отправляет уведомление в Telegram через BackgroundTasks.
    """
    logger.info(f"📦 Создание заказа для пользователя {user.id}")

    try:
        order = await create_order(session, user.id, order_data)
        logger.info(
            f"✅ Заказ #{order.id} успешно создан на сумму {order.total_amount} шмеклей"
        )

        # Отправляем уведомление в Telegram в фоновом режиме
        background_tasks.add_task(
            send_order_notification,
            order_id=order.id,
            total_amount=order.total_amount,
            user_email=user.email,
            delivery_address=order.delivery_address,
        )

        return order
    except ValueError as e:
        logger.error(f"❌ Ошибка создания заказа: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=List[OrderRead],
    summary="Получить историю заказов",
    description="Возвращает все заказы текущего пользователя (сортировка по дате, новые сверху)",
)
async def get_my_orders(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Получить список всех заказов текущего пользователя.
    """
    logger.info(f"📜 Запрос истории заказов для пользователя {user.id}")

    orders = await get_user_orders(session, user.id)

    logger.info(f"✅ Найдено {len(orders)} заказов для пользователя {user.id}")
    return orders


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Получить детали заказа",
    description="Возвращает полную информацию о конкретном заказе с товарами (frozen_price, frozen_name)",
)
async def get_order_details(
    order_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user),
):
    """
    Получить детали конкретного заказа.
    Доступ только к собственным заказам.
    """
    logger.info(f"🔍 Запрос деталей заказа #{order_id} для пользователя {user.id}")

    order = await get_order_by_id(session, user.id, order_id)

    if order is None:
        logger.warning(f"❌ Заказ #{order_id} не найден или недоступен")
        raise HTTPException(
            status_code=404, detail=f"Заказ #{order_id} не найден или недоступен"
        )

    logger.info(f"✅ Заказ #{order_id} найден")
    return order
