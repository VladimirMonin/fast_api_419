"""
Модуль для работы с погодой через OpenWeatherMap API.
Учебный пример использования внешнего API и HTMX автообновления.
"""

import asyncio
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter()

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Конфигурация OpenWeatherMap
OPENWEATHER_API_KEY = "2222"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
CITY = "Усть-Каменогорск"


@router.get("/weather", response_class=HTMLResponse)
async def weather_page(request: Request):
    """
    Отображает страницу с погодой.

    Args:
        request: FastAPI Request объект

    Returns:
        HTMLResponse: Рендер шаблона weather.html
    """
    return templates.TemplateResponse(
        "weather.html",
        {
            "request": request,
            "city": CITY,
        },
    )


@router.get("/weather/data", response_class=HTMLResponse)
async def weather_data(request: Request):
    """
    Получает актуальные данные о погоде и возвращает HTML-фрагмент.
    Используется для HTMX автообновления.

    Args:
        request: FastAPI Request объект

    Returns:
        HTMLResponse: Рендер шаблона partials/weather_data.html
    """
    try:
        # 🎬 Имитация задержки для демонстрации анимации загрузки
        logger.info("⏳ Начинаем загрузку данных о погоде (с задержкой 5 сек)...")
        await asyncio.sleep(2)

        # Запрос к OpenWeatherMap API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                OPENWEATHER_URL,
                params={
                    "q": CITY,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "ru",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            weather_data = response.json()

        logger.info(f"✅ Получены данные о погоде для {CITY}")

        # Извлекаем нужные данные
        context = {
            "request": request,
            "city": weather_data.get("name", CITY),
            "temp": round(weather_data["main"]["temp"]),
            "feels_like": round(weather_data["main"]["feels_like"]),
            "description": weather_data["weather"][0]["description"].capitalize(),
            "icon": weather_data["weather"][0]["icon"],
            "humidity": weather_data["main"]["humidity"],
            "pressure": weather_data["main"]["pressure"],
            "wind_speed": round(weather_data["wind"]["speed"], 1),
            "clouds": weather_data["clouds"]["all"],
        }

        return templates.TemplateResponse("partials/weather_data.html", context)

    except httpx.HTTPError as e:
        logger.error(f"❌ Ошибка при запросе к OpenWeatherMap API: {e}")
        return templates.TemplateResponse(
            "partials/weather_data.html",
            {
                "request": request,
                "error": "Не удалось получить данные о погоде",
            },
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return templates.TemplateResponse(
            "partials/weather_data.html",
            {
                "request": request,
                "error": "Произошла ошибка при обработке данных",
            },
        )
