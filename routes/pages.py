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
    session: AsyncSession = Depends(get_db_session)
):
    """
    Главная страница - каталог товаров
    
    include_in_schema=False скрывает этот эндпоинт из OpenAPI документации,
    так как он возвращает HTML, а не JSON
    """
    # Получаем все товары из базы данных
    products = await products_get_with_filters(session)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
        }
    )
