"""
Роуты для HTML-страниц (Jinja2 templates)
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index(request: Request):
    """
    Главная страница - каталог товаров
    
    include_in_schema=False скрывает этот эндпоинт из OpenAPI документации,
    так как он возвращает HTML, а не JSON
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": "Привет из Jinja2! 👋"
        }
    )
