"""
Роуты для HTML-страниц (Jinja2 templates)
"""
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, products_get_with_filters

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index(
    request: Request, 
    session: AsyncSession = Depends(get_db_session),
    search: str | None = None
):
    """
    Главная страница - каталог товаров
    
    Параметры:
    - search: Поисковый запрос для фильтрации товаров по названию и описанию
    
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
        }
    )
