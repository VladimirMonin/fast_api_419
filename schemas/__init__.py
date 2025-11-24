# schemas/__init__.py
"""
Экспорт всех Pydantic схем для централизованного доступа.
"""

from schemas.commerce import (
    CartItemBatch,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
    OrderCreate,
    OrderItemRead,
    OrderRead,
    ProductInCart,
)
from schemas.product import (
    Category,
    CategoryCreate,
    Product,
    ProductCreate,
    ProductUpdate,
    Tag,
    TagCreate,
)
from schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    # Product schemas
    "Category",
    "CategoryCreate",
    "Tag",
    "TagCreate",
    "Product",
    "ProductCreate",
    "ProductUpdate",
    # User schemas
    "UserCreate",
    "UserRead",
    "UserUpdate",
    # Commerce schemas
    "CartItemCreate",
    "CartItemUpdate",
    "CartItemRead",
    "CartRead",
    "CartItemBatch",
    "ProductInCart",
    "OrderCreate",
    "OrderRead",
    "OrderItemRead",
]
