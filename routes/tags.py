# routes/tags.py
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import (
    get_db_session,
    tag_create,
    tag_delete,
    tag_get_by_id,
    tags_get_all,
    tag_update,
)
from schemas.product import Tag, TagCreate


router = APIRouter()


@router.get(
    "/",
    response_model=List[Tag],
    summary="Получить список всех тегов",
    description="Возвращает список всех тегов с возможностью пагинации.",
)
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получить список всех тегов.

    - **skip**: Количество тегов для пропуска (пагинация)
    - **limit**: Максимальное количество тегов для возврата
    """
    try:
        tags = await tags_get_all(session)
        return tags[skip : skip + limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка тегов: {e}",
        )


@router.get(
    "/{tag_id}",
    response_model=Tag,
    summary="Получить тег по ID",
    description="Возвращает конкретный тег по его уникальному идентификатору.",
)
async def get_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получить конкретный тег по его ID.

    - **tag_id**: Уникальный идентификатор тега
    """
    try:
        tag = await tag_get_by_id(session, tag_id)
        return tag
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тег с ID {tag_id} не найден",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении тега: {e}",
        )


@router.post(
    "/",
    response_model=Tag,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый тег",
    description="Создаёт новый тег. Имя тега должно быть уникальным.",
)
async def create_tag(
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Создать новый тег.

    - **name**: Название тега (от 2 до 30 символов)
    """
    try:
        new_tag = await tag_create(session, tag_data)
        return new_tag
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании тега: {e}",
        )


@router.put(
    "/{tag_id}",
    response_model=Tag,
    summary="Обновить тег",
    description="Выполняет полное обновление тега по ID.",
)
async def update_tag(
    tag_id: int,
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Полное обновление тега.

    - **tag_id**: ID тега для обновления
    - **name**: Новое название тега
    """
    try:
        # Обновляем тег (функция tag_get_by_id вызовется внутри tag_update)
        tag_to_update = Tag(id=tag_id, name=tag_data.name)
        updated_tag = await tag_update(session, tag_to_update)
        return updated_tag

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тег с ID {tag_id} не найден",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении тега: {e}",
        )


@router.delete(
    "/{tag_id}",
    summary="Удалить тег",
    description="Удаляет тег по ID. Связи с продуктами удаляются автоматически.",
)
async def delete_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Удалить тег по ID.

    - **tag_id**: ID тега для удаления

    Возвращает сообщение об успешном удалении.
    Связи many-to-many с продуктами удаляются автоматически.
    """
    try:
        # Проверяем существование тега
        await tag_get_by_id(session, tag_id)

        # Удаляем тег (связи в промежуточной таблице удалятся автоматически)
        await tag_delete(session, tag_id)

        return {
            "message": f"Тег с ID {tag_id} успешно удалён",
            "deleted_id": tag_id,
        }

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тег с ID {tag_id} не найден",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении тега: {e}",
        )
