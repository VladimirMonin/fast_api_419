# routes/categories.py
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import (
    get_db_session,
    category_create,
    category_delete,
    category_get_by_id,
    categories_get_all,
    category_update,
    category_has_products,
)
from schemas.product import Category, CategoryCreate


router = APIRouter()


@router.get(
    "/",
    response_model=List[Category],
    summary="Получить список всех категорий",
    description="Возвращает список всех категорий с возможностью пагинации.",
)
async def list_categories(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получить список всех категорий.

    - **skip**: Количество категорий для пропуска (пагинация)
    - **limit**: Максимальное количество категорий для возврата
    """
    try:
        categories = await categories_get_all(session)
        return categories[skip : skip + limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка категорий: {e}",
        )


@router.get(
    "/{category_id}",
    response_model=Category,
    summary="Получить категорию по ID",
    description="Возвращает конкретную категорию по её уникальному идентификатору.",
)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получить конкретную категорию по её ID.

    - **category_id**: Уникальный идентификатор категории
    """
    try:
        category = await category_get_by_id(session, category_id)
        return category
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категория с ID {category_id} не найдена",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении категории: {e}",
        )


@router.post(
    "/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую категорию",
    description="Создаёт новую категорию. Имя категории должно быть уникальным.",
)
async def create_category(
    category_data: CategoryCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Создать новую категорию.

    - **name**: Название категории (от 3 до 50 символов)
    """
    try:
        new_category = await category_create(session, category_data)
        return new_category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании категории: {e}",
        )


@router.put(
    "/{category_id}",
    response_model=Category,
    summary="Обновить категорию",
    description="Выполняет полное обновление категории по ID.",
)
async def update_category(
    category_id: int,
    category_data: CategoryCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Полное обновление категории.

    - **category_id**: ID категории для обновления
    - **name**: Новое название категории
    """
    try:
        # Обновляем категорию (функция category_get_by_id вызовется внутри category_update)
        category_to_update = Category(id=category_id, name=category_data.name)
        updated_category = await category_update(session, category_to_update)
        return updated_category

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категория с ID {category_id} не найдена",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении категории: {e}",
        )


@router.delete(
    "/{category_id}",
    summary="Удалить категорию",
    description="Удаляет категорию по ID. Нельзя удалить категорию, если к ней привязаны продукты.",
)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Удалить категорию по ID.

    - **category_id**: ID категории для удаления

    Возвращает сообщение об успешном удалении.
    """
    try:
        # Проверяем существование категории
        await category_get_by_id(session, category_id)

        # Проверяем наличие связанных продуктов через функцию из database.py
        has_products = await category_has_products(session, category_id)

        if has_products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить категорию: существуют связанные продукты",
            )

        # Удаляем категорию
        await category_delete(session, category_id)

        return {
            "message": f"Категория с ID {category_id} успешно удалена",
            "deleted_id": category_id,
        }

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категория с ID {category_id} не найдена",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении категории: {e}",
        )
