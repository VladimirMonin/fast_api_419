# lesson_1.py
from datetime import datetime
from pydantic import BaseModel, ValidationError

# 1. Определяем модель Пользователь
class User(BaseModel):
    id: int
    username: str
    signup_ts: datetime | None = None
    friends: list[int] = []

# 2. Создаём "сырые" данные, как будто они пришли из внешнего источника (например, JSON)
external_data = {
    'id': '123',  # Обратите внимание, id - это строка, а не число
    'username': 'сидор_петров',
    'signup_ts': '2025-10-01T12:00:00',
    'friends': [1, '2', 3] # Список содержит и числа, и строки
}

# 3. Можем не создавать напрямую экземпляр User, а использовать метод валидации model_validate
try:
    user = User.model_validate(external_data)
    print(f'Пользователь создан: {user}')

    # Смотрим на методы модели model_dump и model_dump_json
    user_dict = user.model_dump()  # Конвертация в словарь
    print(f'Пользователь в виде словаря: {user_dict}')

    user_json = user.model_dump_json(indent=4)  # Конвертация в JSON строку
    print(f'Пользователь в виде JSON: {user_json}')

except Exception as e:
    print(f'Ошибка валидации данных: {e}')


import json
# Как конвертируется кириллица без ASCI=False
# "\u0421\u0438\u0434\u043e\u0440 \u041f\u0435\u0442\u0440\u043e\u0432"
print(json.dumps("Сидор Петров", indent=4))


# 5. Пример с невалидными данными
invalid_data = {
    'id': 'банан',  # Невозможно конвертировать в int
    'username': 'jane.doe'
}

print("\n--- Попытка создать пользователя с неверными данными ---")
try:
    User.model_validate(invalid_data)
except ValidationError as e:
    print("Произошла ошибка валидации:")
    print(e)