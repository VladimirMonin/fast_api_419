# models/product.py
from typing import List, Optional
from sqlalchemy import Column, Table, String, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Базовый класс для моделей из того же пакета
from models.base import Base


# --- Ассоциативная таблица M2M ---
product_tag_association = Table(
    "product_tag_association",
    Base.metadata,
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # Связь один-ко-многим с продуктами
    products: Mapped[List["Product"]] = relationship(
        back_populates="category",
        lazy="raise_on_sql",  # Защита от ленивой загрузки в async
        cascade="save-update, merge",  # Безопасный каскад
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Связь многие-ко-многим с продуктами
    products: Mapped[List["Product"]] = relationship(
        secondary=product_tag_association,
        back_populates="tags",
        lazy="raise_on_sql",  # Защита от ленивой загрузки в async
        cascade="save-update, merge",  # ✅ Правильный каскад для M2M
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Индекс для поиска по LIKE/ILIKE
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Text для длинных описаний, может быть NULL
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # URL может быть пустым
    image_url: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Индексы на цены для фильтрации
    price_shmeckles: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    price_flurbos: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # --- Связи ---

    # Внешний ключ на категорию (может быть NULL)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,  # Критично для JOIN'ов
    )

    # Связь многие-к-одному с категорией
    category: Mapped[Optional["Category"]] = relationship(
        back_populates="products",
        lazy="raise_on_sql",
    )

    # Связь многие-ко-многим с тегами
    tags: Mapped[List["Tag"]] = relationship(
        secondary=product_tag_association,
        back_populates="products",
        lazy="raise_on_sql",
        cascade="save-update, merge",  # ✅ Безопасно для M2M
    )

    # Составной индекс для частых запросов
    __table_args__ = (
        Index("ix_product_category_price", "category_id", "price_shmeckles"),
    )
