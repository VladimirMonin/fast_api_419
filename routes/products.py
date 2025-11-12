# routes/products.py
import logging
from typing import List, Optional

from schemas.product import Product, ProductCreate, ProductUpdate
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile
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

logger = logging.getLogger(__name__)

# --- Маршруты API для работы с товарами ---

router = APIRouter()


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
    logger.info(f"📥 Запрос на получение товара ID={product_id}")

    try:
        product = await product_get_by_id(session, product_id)
        logger.info(f"✅ Товар ID={product_id} успешно получен")
        return product
    except Exception as e:
        logger.error(f"❌ Ошибка при получении товара ID={product_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


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
    logger.info(
        f"📥 Запрос списка товаров (search={search}, sort={sort}, has_image={has_image})"
    )

    try:
        products = await products_get_with_filters(
            session, search=search, sort=sort, has_image=has_image
        )
        logger.info(f"✅ Список товаров получен, найдено: {len(products)}")
        return products
    except ValueError as e:
        logger.error(f"❌ Ошибка валидации при получении списка товаров: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка товаров: {e}")
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
    logger.info(f"📥 Запрос на создание товара: {product.name}")

    try:
        new_product = await product_create(session, product)
        logger.info(f"✅ Товар создан: ID={new_product.id}, Name={new_product.name}")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании товара: {e}")
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
    logger.info(
        f"📤 Добавлена фоновая задача отправки уведомления в Telegram для товара ID={new_product.id}"
    )
    background_tasks.add_task(send_telegram_message, telegram_message)

    return new_product


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
    logger.info(f"📥 Запрос на обновление товара ID={product_id}")

    try:
        # Создаем объект ProductUpdate с ID из URL и данными из тела запроса
        product_update_data = ProductUpdate(
            id=product_id, **updated_product.model_dump()
        )
        product = await product_update(session, product_update_data)
        logger.info(f"✅ Товар ID={product_id} успешно обновлён")
        return product
    except ValueError as e:
        logger.error(f"❌ Товар ID={product_id} не найден: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении товара ID={product_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обновлении товара: {e}"
        )


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
    logger.info(f"📥 Запрос на удаление товара ID={product_id}")

    try:
        await product_delete(session, product_id)
        logger.info(f"✅ Товар ID={product_id} успешно удалён")
        return product_id
    except ValueError as e:
        logger.error(f"❌ Товар ID={product_id} не найден: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении товара ID={product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении товара: {e}")


@router.post(
    "/{product_id}/upload-image",
    summary="Загрузить изображение для товара",
    tags=["Products"],
)
async def upload_product_image(
    product_id: int,
    file: UploadFile,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Загружает изображение для товара.
    Заменяет старое изображение, если оно существует.

    - **product_id**: ID товара
    - **file**: Файл изображения (JPG, PNG, GIF, WEBP, макс 5MB)
    """
    from core.storage import save_product_image, delete_product_image

    logger.info(f"📥 Запрос на загрузку изображения для товара ID={product_id}")

    # Проверяем существование товара
    try:
        product = await product_get_by_id(session, product_id)
    except Exception as e:
        logger.error(f"❌ Товар ID={product_id} не найден: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    # Удаляем старое изображение, если оно есть
    if product.image_url:
        logger.info(f"🗑️ Удаление старого изображения: {product.image_url}")
        delete_product_image(product.image_url)

    # Сохраняем новое изображение
    try:
        image_url = await save_product_image(file)
        logger.info(f"✅ Изображение сохранено: {image_url}")
    except HTTPException:
        logger.info("❌ Ошибка при сохранении изображения, прерывание операции")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении изображения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {e}")

    # Обновляем URL в базе данных
    from sqlalchemy import update
    from models.product import Product as ProductModel

    try:
        await session.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(image_url=image_url)
        )
        await session.commit()
        logger.info(f"✅ URL изображения обновлён в БД для товара ID={product_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {e}")

    return {
        "product_id": product_id,
        "image_url": image_url,
        "message": "✅ Изображение успешно загружено",
    }


@router.delete(
    "/{product_id}/image",
    summary="Удалить изображение товара",
    tags=["Products"],
)
async def delete_product_image_endpoint(
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Удаляет изображение товара из файловой системы и БД.
    """
    from core.storage import delete_product_image
    from sqlalchemy import update
    from models.product import Product as ProductModel

    logger.info(f"📥 Запрос на удаление изображения товара ID={product_id}")

    # Проверяем существование товара
    try:
        product = await product_get_by_id(session, product_id)
    except Exception as e:
        logger.error(f"❌ Товар ID={product_id} не найден: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    if not product.image_url:
        logger.warning(f"⚠️ У товара ID={product_id} нет изображения")
        raise HTTPException(status_code=404, detail="У товара нет изображения")

    # Удаляем файл
    deleted = delete_product_image(product.image_url)
    if not deleted:
        logger.warning(f"⚠️ Файл не найден: {product.image_url}")

    # Обновляем БД
    try:
        await session.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(image_url=None)
        )
        await session.commit()
        logger.info(f"✅ Изображение удалено для товара ID={product_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {e}")

    return {"message": "✅ Изображение удалено", "product_id": product_id}
