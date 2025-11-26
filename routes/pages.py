"""
Роуты для HTML-страниц (Jinja2 templates)
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user_from_cookie
from core.database import get_db_session, products_get_with_filters, product_get_by_id
from models.user import User

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User | None = Depends(get_current_user_from_cookie),
    search: str | None = None,
):
    """
    Главная страница - каталог товаров

    Параметры:
    - search: Поисковый запрос для фильтрации товаров по названию и описанию
    - user: Текущий пользователь (если авторизован)

    include_in_schema=False скрывает этот эндпоинт из OpenAPI документации,
    так как он возвращает HTML, а не JSON
    """
    # Получаем товары из базы данных с учетом поискового запроса
    products = await products_get_with_filters(session, search=search)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "user": user,
        },
    )


@router.get("/product/{product_id}", include_in_schema=False)
async def get_product_card(
    request: Request,
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User | None = Depends(get_current_user_from_cookie),
):
    """
    Получение обновленной карточки товара по ID

    Используется для HTMX-обновления отдельной карточки без перезагрузки страницы.
    Возвращает только HTML фрагмент карточки товара.
    """
    try:
        product = await product_get_by_id(session, product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return templates.TemplateResponse(
        "partials/product_card.html",
        {
            "request": request,
            "product": product,
            "user": user,
        },
    )
