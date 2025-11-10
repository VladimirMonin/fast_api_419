# routes/products.py
from typing import List

import telegram
from schemas.product import Product, ProductCreate
from data import products
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from utils.telegram_bot import send_telegram_message
from core.database import (
    get_db_session,
    tag_create,
    category_create,
    product_create,
    category_delete,
    tag_delete,
    product_delete,
    category_get_by_id,
    tag_get_by_id,
    product_get_by_id,
    categories_get_all,
    tags_get_all,
    products_get_all,
    products_get_like_name,
    category_update,
    tag_update,
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
async def list_products(search: str = "", sort: str = "", has_image: bool = False):
    """
    Возвращает список всех товаров с возможностью фильтрации и сортировки.
    - **search**: Поиск по названию и описанию товара.
    - **sort**: Сортировка по цене. Формат: `currency_direction` (например, `credits_asc`, `shmeckles_desc`).
    - **has_image**: Если True, возвращаются только товары с изображениями.
    """
    filtered_products = products
    # products/?search=ПлЮмБуС
    # Фильтрация по поисковому запросу
    if search:
        filtered_products = [
            item
            for item in filtered_products
            if search.lower() in item["name"].lower()
            or search.lower() in item["description"].lower()
        ]

    # Фильтрация по наличию изображения
    if has_image:
        filtered_products = [item for item in filtered_products if item["image_url"]]

    # Сортировка по цене
    # products/?sort=credits_asc
    # products/?sort=shmeckles_desc
    if sort:
        try:
            currency, direction = sort.split("_")
            reverse = direction == "desc"
            # sort - метод списка
            # key - ключ сортировки, принимает функцию
            # item - каждый словарь с товаром
            # item["prices"] - вложенный словарь с ценами
            # currency - ключ валюты из параметра запроса
            # float('inf') - бесконечность, чтобы товары без указанной валюты оказались в конце списка

            filtered_products.sort(
                key=lambda item: item["prices"].get(currency, float("inf")),
                reverse=reverse,
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат параметра sort. Используйте 'currency_direction'.",
            )

    return filtered_products


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
    "/update/{product_id}",
    response_model=Product,
    summary="Обновить данные о товаре",
)
async def update_product(product_id: int, updated_product: ProductCreate):
    """
    Обновляет данные о товаре по его ID.
    """
    # Формируем кортеж формата (индекс, товар) для каждого товара в списке
    for index, item in enumerate(products):
        # Мы нашли нужный товар по ID
        if item["id"] == product_id:
            # Обновляем товар, сохраняя его ID
            updated_data = updated_product.model_dump()
            updated_data["id"] = product_id
            products[index] = updated_data
            return products[index]
    raise HTTPException(status_code=404, detail="Товар не найден")


# DELETE
@router.delete(
    "/delete/{product_id}",
    response_model=int,
    summary="Удалить товар",
)
async def delete_product(product_id: int):
    """
    Удаляет товар по его ID.
    """
    for index, item in enumerate(products):
        if item["id"] == product_id:
            products.pop(index)
            return product_id
    raise HTTPException(status_code=404, detail="Товар не найден")
