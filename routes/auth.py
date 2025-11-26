"""
Модуль HTML роутов для аутентификации.

Этот модуль содержит роуты для работы с формами входа и регистрации
через HTML интерфейс с использованием HTMX.

Основные роуты:
    - GET /auth/login-page - Страница входа/регистрации
    - POST /auth/login-form - Обработка формы входа (устанавливает cookie)
    - POST /auth/register-form - Обработка формы регистрации
    - GET /auth/logout - Выход из системы (удаляет cookie)
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy.ext.asyncio import AsyncSession

from auth.backend import get_jwt_strategy
from auth.dependencies import get_current_user_from_cookie
from auth.manager import get_user_manager, UserManager
from core.database import get_db_session
from models.user import User
from schemas.user import UserCreate

router = APIRouter()

# Определение базовой директории и шаблонов
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login-page", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: User | None = Depends(get_current_user_from_cookie),
):
    """
    Отображает страницу входа и регистрации.

    Если пользователь уже авторизован, редиректит на главную страницу.

    Args:
        request: FastAPI Request объект
        user: Текущий пользователь из cookie (если есть)

    Returns:
        HTMLResponse: Рендер шаблона auth.html или редирект на главную
    """
    # Если пользователь уже вошел, перенаправляем на главную
    if user:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "auth.html",
        {"request": request, "user": user},
    )


@router.post("/login-form")
async def login(
    response: Response,
    username: str = Form(...),  # email пользователя (OAuth2 требует username)
    password: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Обрабатывает форму входа и устанавливает JWT токен в cookies.

    Процесс:
    1. Аутентифицирует пользователя по email и паролю
    2. Создает JWT токен
    3. Устанавливает токен в cookie "access_token"
    4. Возвращает редирект на главную страницу

    Args:
        response: FastAPI Response для установки cookies
        username: Email пользователя (поле называется username для совместимости с OAuth2)
        password: Пароль пользователя
        session: Асинхронная сессия БД
        user_manager: Менеджер пользователей

    Returns:
        HTMLResponse: Сообщение об успехе с заголовком HX-Redirect для HTMX

    Raises:
        HTTPException: Если учетные данные неверны
    """
    # Получаем пользователя по email
    user = await user_manager.get_by_email(username)

    # Проверяем существование пользователя и правильность пароля
    if (
        user is None
        or not user_manager.password_helper.verify_and_update(
            password, user.hashed_password
        )[0]
    ):
        # Возвращаем ошибку для HTMX
        return HTMLResponse(
            content="""
            <div class="alert alert-danger" role="alert">
                ❌ Неверный email или пароль
            </div>
            """,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Создаем JWT токен
    strategy = get_jwt_strategy()
    token = await strategy.write_token(user)

    # Устанавливаем токен в cookie
    response = HTMLResponse(
        content="""
        <div class="alert alert-success" role="alert">
            ✅ Вход выполнен успешно! Перенаправление...
        </div>
        """,
        headers={"HX-Redirect": "/"},
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # Защита от XSS атак
        max_age=3600,  # 1 час
        samesite="lax",  # Защита от CSRF
    )

    return response


@router.post("/register-form")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Обрабатывает форму регистрации нового пользователя.

    Процесс:
    1. Проверяет совпадение паролей
    2. Создает нового пользователя
    3. Возвращает сообщение об успехе

    Args:
        request: FastAPI Request объект
        email: Email нового пользователя
        password: Пароль
        password_confirm: Подтверждение пароля
        user_manager: Менеджер пользователей

    Returns:
        HTMLResponse: Сообщение об успехе или ошибке

    Raises:
        UserAlreadyExists: Если пользователь с таким email уже существует
    """
    # Проверка совпадения паролей
    if password != password_confirm:
        return HTMLResponse(
            content="""
            <div class="alert alert-danger" role="alert">
                ❌ Пароли не совпадают
            </div>
            """,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Создание схемы пользователя
    user_create = UserCreate(email=email, password=password)

    try:
        # Создание пользователя через UserManager
        user = await user_manager.create(user_create, safe=True, request=request)

        return HTMLResponse(
            content=f"""
            <div class="alert alert-success" role="alert">
                ✅ Регистрация успешна! Теперь войдите с email: {user.email}
            </div>
            <script>
                // Автоматически переключаем на вкладку входа через 2 секунды
                setTimeout(() => {{
                    document.getElementById('login-tab').click();
                }}, 2000);
            </script>
            """,
        )

    except UserAlreadyExists:
        return HTMLResponse(
            content="""
            <div class="alert alert-danger" role="alert">
                ❌ Пользователь с таким email уже существует
            </div>
            """,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <div class="alert alert-danger" role="alert">
                ❌ Ошибка регистрации: {str(e)}
            </div>
            """,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/logout")
async def logout(response: Response):
    """
    Выход из системы - удаляет cookie с токеном.

    Args:
        response: FastAPI Response для удаления cookies

    Returns:
        RedirectResponse: Редирект на страницу входа
    """
    response = RedirectResponse("/auth/login-page", status_code=status.HTTP_302_FOUND)

    # Удаляем cookie с токеном
    response.delete_cookie(key="access_token")

    return response
