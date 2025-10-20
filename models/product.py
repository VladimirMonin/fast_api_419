# models/product.py
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

# Базовый класс для моделей из того же пакета
from models.base import Base


class Product(Base):
    """
    Модель товара
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str] = mapped_column(String(200), nullable=False)
    price_shmeckles: Mapped[float] = mapped_column(Float, nullable=False)
    price_flurbos: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name}>"
