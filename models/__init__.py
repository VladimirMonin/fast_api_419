# models/__init__.py
"""
Экспорт всех моделей для централизованного доступа.
Это необходимо для Alembic autogenerate.
"""

from models.base import Base
from models.commerce import Cart, CartItem, Order, OrderItem
from models.product import Category, Product, Tag, product_tag_association
from models.user import User

__all__ = [
    "Base",
    "User",
    "Category",
    "Tag",
    "Product",
    "product_tag_association",
    "Cart",
    "CartItem",
    "Order",
    "OrderItem",
]
