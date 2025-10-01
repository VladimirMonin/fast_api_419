from fastapi import FastAPI

# Создаем экземпляр FastAPI
app = FastAPI()

# Определяем корневой маршрут
@app.get("/")
async def read_root():
    # 1. Автоматически конвертация в JSON
    # 2. Формируется ответ с кодом 200 OK
    return {"Hello": "World"}