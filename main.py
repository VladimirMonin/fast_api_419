from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


# --- Модель данных (обычно выносится в отдельный файл) ---
class User(BaseModel):
    id: int
    username: str
    friends: list[int] = []


# --- "База данных" в памяти для нашего примера ---
# Ключ - ID пользователя, значение - объект User
fake_users_db: dict[int, User] = {}

# --- Приложение FastAPI ---
app = FastAPI()


@app.post("/users/", response_model=User)
async def create_user(user: User):
    """
    Создаёт нового пользователя и сохраняет его в "базе данных".
    """
    fake_users_db[user.id] = user
    return user


@app.get("/users/", response_model=List[User])
async def get_users():
    """
    Возвращает список всех пользователей.
    """
    return list(fake_users_db.values())
