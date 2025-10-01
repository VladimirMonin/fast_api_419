from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List


# --- Модель данных (обычно выносится в отдельный файл) ---
class User(BaseModel):
    id: int = Field(..., example=1, description="Уникальный идентификатор пользователя")
    username: str = Field(..., example="ivan_ivanych", description="Имя пользователя")
    friends: list[int] = Field(default_factory=list, example=[1, 2, 3], description="Список ID друзей")


# --- "База данных" в памяти для нашего примера ---
# Ключ - ID пользователя, значение - объект User
fake_users_db: dict[int, User] = {}

# --- Приложение FastAPI ---
app = FastAPI(
    title="Учебное приложение Python419",
    description="Пример простого API для управления пользователями",
    version="1.0.0"
)


@app.post("/users/", response_model=User, status_code=201, summary="Создать пользователя", tags=["Пользователи"])
async def create_user(user: User):
    """
    Создаёт нового пользователя и сохраняет его в "базе данных".
    """
    fake_users_db[user.id] = user
    return user


@app.get("/users/", response_model=List[User], summary="Получить всех пользователей", tags=["Пользователи"])
async def get_users():
    """
    Возвращает список всех пользователей.
    """
    return list(fake_users_db.values())
