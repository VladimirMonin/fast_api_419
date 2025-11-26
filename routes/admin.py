"""
Модуль роутов для админ-панели.

Этот модуль содержит роуты для управления товарами админами:
    - GET /admin/products/new - Форма создания товара
    - POST /admin/products/new - Создание нового товара
    - GET /admin/products/{id}/edit - Форма редактирования товара (HTMX)
    - POST /admin/products/{id}/edit - Сохранение изменений товара (HTMX)
"""

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user_from_cookie
from core.database import (
    categories_get_all,
    get_db_session,
    product_create,
    product_get_by_id,
    tags_get_all,
)
from models.user import User
from schemas.product import ProductCreate

router = APIRouter()

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def require_superuser(user: User | None = Depends(get_current_user_from_cookie)):
    """
    Зависимость для проверки прав администратора.

    Args:
        user: Текущий пользователь из cookie

    Returns:
        User: Объект пользователя-администратора

    Raises:
        HTTPException: Если пользователь не авторизован или не является админом
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация",
        )

    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуются права администратора.",
        )

    return user


@router.get("/admin/products/new", response_class=HTMLResponse)
async def new_product_form(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_superuser),
):
    """
    Отображает форму для создания нового товара.

    Доступно только для администраторов (is_superuser=True).

    Args:
        request: FastAPI Request объект
        session: Асинхронная сессия БД
        user: Авторизованный пользователь-администратор

    Returns:
        HTMLResponse: Рендер шаблона admin_product.html
    """
    # Получаем все категории и теги для выпадающих списков
    categories = await categories_get_all(session)
    tags = await tags_get_all(session)

    return templates.TemplateResponse(
        "admin_product.html",
        {
            "request": request,
            "user": user,
            "categories": categories,
            "tags": tags,
            "product": None,  # Для создания нового товара
            "product_tag_ids": [],
        },
    )


@router.post("/admin/products/new")
async def create_product(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_superuser),
    name: str = Form(...),
    description: str = Form(""),
    price_shmeckles: float = Form(...),
    price_flurbos: float = Form(...),
    image_url: str = Form(""),
    category_id: int | None = Form(None),
    tag_ids: List[int] = Form([]),
):
    """
    Создает новый товар в базе данных.

    Доступно только для администраторов.

    Args:
        request: FastAPI Request объект
        session: Асинхронная сессия БД
        user: Авторизованный пользователь-администратор
        name: Название товара
        description: Описание товара
        price_shmeckles: Цена в шмекелях
        price_flurbos: Цена в флурбо
        image_url: URL картинки
        category_id: ID категории (опционально)
        tag_ids: Список ID тегов

    Returns:
        RedirectResponse: Редирект на главную страницу после создания
    """
    # Создаем схему для валидации
    product_data = ProductCreate(
        name=name,
        description=description or None,
        price_shmeckles=price_shmeckles,
        price_flurbos=price_flurbos,
        image_url=image_url or None,
        category_id=category_id,
        tag_ids=tag_ids,
    )

    # Создаем товар в БД
    await product_create(session, product_data)
    await session.commit()

    # Редирект на главную страницу
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(
    request: Request,
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_superuser),
):
    """
    Отображает форму редактирования товара (для HTMX).

    Доступно только для администраторов.

    Args:
        request: FastAPI Request объект
        product_id: ID товара для редактирования
        session: Асинхронная сессия БД
        user: Авторизованный пользователь-администратор

    Returns:
        HTMLResponse: Рендер формы редактирования
    """
    try:
        product = await product_get_by_id(session, product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Получаем все категории и теги
    categories = await categories_get_all(session)
    tags = await tags_get_all(session)

    # Получаем ID тегов товара
    product_tag_ids = [tag.id for tag in product.tags]

    return templates.TemplateResponse(
        "partials/product_edit_form.html",
        {
            "request": request,
            "user": user,
            "categories": categories,
            "tags": tags,
            "product": product,
            "product_tag_ids": product_tag_ids,
        },
    )


@router.post("/admin/products/{product_id}/edit", response_class=HTMLResponse)
async def update_product(
    request: Request,
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_superuser),
    name: str = Form(...),
    description: str = Form(""),
    price_shmeckles: float = Form(...),
    price_flurbos: float = Form(...),
    image_url: str = Form(""),
    category_id: int | None = Form(None),
    tag_ids: List[int] = Form([]),
):
    """
    Обновляет данные товара (HTMX).

    Доступно только для администраторов.

    Args:
        request: FastAPI Request объект
        product_id: ID товара для обновления
        session: Асинхронная сессия БД
        user: Авторизованный пользователь-администратор
        name: Новое название товара
        description: Новое описание товара
        price_shmeckles: Новая цена в шмекелях
        price_flurbos: Новая цена в флурбо
        image_url: Новый URL картинки
        category_id: Новый ID категории
        tag_ids: Новый список ID тегов

    Returns:
        HTMLResponse: Обновленная карточка товара
    """
    try:
        # Получаем товар из БД (ORM модель)
        from sqlalchemy import select
        from models.product import Product as ProductORM, Tag as TagORM

        stmt = select(ProductORM).where(ProductORM.id == product_id)
        result = await session.execute(stmt)
        product_orm = result.scalar_one_or_none()

        if not product_orm:
            raise HTTPException(status_code=404, detail="Товар не найден")

        # Обновляем поля
        product_orm.name = name
        product_orm.description = description or None
        product_orm.price_shmeckles = price_shmeckles
        product_orm.price_flurbos = price_flurbos
        product_orm.image_url = image_url or None
        product_orm.category_id = category_id

        # Обновляем теги
        if tag_ids:
            tags_stmt = select(TagORM).where(TagORM.id.in_(tag_ids))
            tags_orm = await session.scalars(tags_stmt)
            product_orm.tags = list(tags_orm.all())
        else:
            product_orm.tags = []

        # Сохраняем изменения
        await session.commit()

        # Получаем обновленный товар для отображения
        product = await product_get_by_id(session, product_id)

        # Возвращаем обновленную карточку товара
        return templates.TemplateResponse(
            "partials/product_card.html",
            {
                "request": request,
                "product": product,
                "user": user,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления товара: {str(e)}",
        )
