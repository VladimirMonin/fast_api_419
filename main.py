from fastapi import FastAPI
from routes import products


# --- Приложение FastAPI ---
app = FastAPI(
    title="Учебное приложение Python419",
    description="Пример простого API для управления пользователями",
    version="2.0.0",
)

app.include_router(products.router, prefix="/products", tags=["Товары"])
