# routes/products.py
from typing import List
from schemas.product import Product, CreateProduct
from data import products
from fastapi import APIRouter, HTTPException, BackgroundTasks
from asyncio import sleep


# Имитация отправки данных в ТГ
async def mock_telegram_notification(product_name: str, product_id: int):
    print(f"[Background Task] Отправка уведомления в Telegram...")
    await sleep(10)  # Имитируем задержку на отправку
    print(
        f"[Background Task] Уведомление успешно отправлено!\nТовар: {product_name} (ID: {product_id})"
    )


# --- Маршруты API для работы с товарами ---

router = APIRouter()


# 1. Получение данных о товаре (детальный просмотр)
@router.get(
    "/{product_id}",
    response_model=Product,
    summary="Получить данные о товаре",
)
async def get_product(product_id: int):
    """
    Возвращает данные о товаре по его ID.
    """
    # product = next((item for item in products if item["id"] == product_id), None)
    # Альтернативный способ поиска товара через list comprehension
    try:
        product = [item for item in products if item["id"] == product_id][0]
    except IndexError:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


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
)
async def create_product(product: CreateProduct, background_tasks: BackgroundTasks):
    """
    Создает новый товар.
    """
    # Так как мы не работаем с БД - нам нужно найти максимальный ID в текущем списке товаров и увеличить его на 1
    new_product_id = max(item["id"] for item in products) + 1 if products else 1

    # Преобразуем модель Pydantic в словарь. Валидация уже выполнена автоматически
    new_product = product.model_dump()
    new_product["id"] = new_product_id
    products.append(new_product)

    # Фоновая задача - имитация отправки уведомления в Telegram
    background_tasks.add_task(
        mock_telegram_notification, new_product["name"], new_product_id
    )

    return new_product


# PUT
@router.put(
    "/update/{product_id}",
    response_model=Product,
    summary="Обновить данные о товаре",
)
async def update_product(product_id: int, updated_product: CreateProduct):
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
