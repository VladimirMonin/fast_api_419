# routes/products.py
from typing import List, Optional

from schemas.product import Product, ProductCreate, ProductUpdate
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from utils.telegram_bot import send_telegram_message
from core.database import (
    get_db_session,
    product_create,
    product_delete,
    product_get_by_id,
    products_get_with_filters,
    product_update,
)
from sqlalchemy.ext.asyncio import AsyncSession
# --- Маршруты API для работы с товарами ---

router = APIRouter()


# 1. Получение данных о товаре (детальный просмотр)
@router.get(
    "/{product_id}",
    response_model=Product,
    summary="Получить данные о товаре",
    tags=["Products"],
)
async def get_product(product_id: int, session: AsyncSession = Depends(get_db_session)):
    """
    Возвращает данные о товаре по его ID.
    """
    # Делаем запрос к бд через product_get_by_id
    try:
        product = await product_get_by_id(session, product_id)
        return product
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# 2. Получение списка всех товаров.
# Параметры запроса - search (поиск по названию и описанию)
# Еще один параметр - sort (сортировка по цене - которая принемает валюту и направление))
# Чекбокс - только с фотографиями
@router.get(
    "/",
    response_model=List[Product],
    summary="Получить список всех товаров",
)
async def list_products(
    session: AsyncSession = Depends(get_db_session),
    search: Optional[str] = None,
    sort: Optional[str] = None,
    has_image: bool = False,
):
    """
    Возвращает список всех товаров с возможностью фильтрации и сортировки.
    - **search**: Поиск по названию и описанию товара.
    - **sort**: Сортировка по цене. Формат: `currency_direction` (например, `credits_asc`, `shmeckles_desc`).
    - **has_image**: Если True, возвращаются только товары с изображениями.
    """
    try:
        products = await products_get_with_filters(
            session, search=search, sort=sort, has_image=has_image
        )
        return products
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении списка товаров: {e}"
        )


@router.post(
    "/",
    response_model=Product,
    summary="Создать новый товар",
    status_code=201,
    tags=["Products"],
)
async def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Создает новый товар.
    """
    # Пытаемся создать новый товар через product_create
    try:
        new_product = await product_create(session, product)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Формируем сообщение для отправки в Telegram
    telegram_message = f"""
*Новый товар в магазине!*
*Название:* {new_product.name}
*ID:* {new_product.id}
*Описание:* {new_product.description}
*Категория:* {new_product.category.name if new_product.category else "Без категории"}
*Теги:* {", ".join(tag.name for tag in new_product.tags) if new_product.tags else "Нет тегов"}
http://127.0.0.1:8000/products/{new_product.id}

```json
{product.model_dump_json(indent=2, ensure_ascii=False)}
```
"""

    # Фоновая задача - отправка уведомления в Telegram
    background_tasks.add_task(send_telegram_message, telegram_message)

    return new_product


# PUT
@router.put(
    "/{product_id}",
    response_model=Product,
    summary="Обновить данные о товаре",
)
async def update_product(
    product_id: int,
    updated_product: ProductCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Обновляет данные о товаре по его ID.
    """
    try:
        # Создаем объект ProductUpdate с ID из URL и данными из тела запроса
        product_update_data = ProductUpdate(
            id=product_id, **updated_product.model_dump()
        )
        product = await product_update(session, product_update_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обновлении товара: {e}"
        )


# DELETE
@router.delete(
    "/{product_id}",
    response_model=int,
    summary="Удалить товар",
)
async def delete_product(
    product_id: int, session: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет товар по его ID.
    """
    try:
        await product_delete(session, product_id)
        return product_id
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении товара: {e}")
