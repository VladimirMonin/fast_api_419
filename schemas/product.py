from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class CategoryBase(BaseModel):
    """Базовая схема для категории."""

    name: str = Field(
        ...,
        description="Название категории",
        example="Портальные пушки",
        min_length=3,
        max_length=50,
    )


class CategoryCreate(CategoryBase):
    """Схема для создания новой категории."""

    pass


class Category(CategoryBase):
    """Схема для отображения категории, включая её ID из базы данных."""

    id: int = Field(..., description="Уникальный идентификатор категории", example=1)

    model_config = ConfigDict(from_attributes=True)


class TagBase(BaseModel):
    """Базовая схема для тега."""

    name: str = Field(
        ...,
        description="Название тега",
        example="Новинка",
        min_length=2,
        max_length=30,
    )


class TagCreate(TagBase):
    """Схема для создания нового тега."""

    pass


class Tag(TagBase):
    """Схема для отображения тега, включая его ID из базы данных."""

    id: int = Field(..., description="Уникальный идентификатор тега", example=101)

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """Схема для создания нового продукта."""

    name: str = Field(
        ...,
        description="Название продукта",
        example="Смартфон 'Космос-X'",
        min_length=3,
        max_length=100,
    )
    description: Optional[str] = Field(
        None,
        description="Подробное описание продукта",
        example="Футуристический смартфон с прозрачным экраном и ИИ-помощником.",
        max_length=1000,
    )
    image_url: Optional[str] = Field(
        None,
        description="URL-адрес изображения продукта",
        example="https://example.com/images/kosmos-x.jpg",
        max_length=255,
    )
    price_shmeckles: float = Field(
        ...,
        description="Цена продукта в Шмеклях",
        example=999.99,
        gt=0,  # gt = greater than
    )
    price_flurbos: float = Field(
        ...,
        description="Цена продукта в Флёрбосах",
        example=120.50,
        gt=0,
    )
    category_id: Optional[int] = Field(
        None,
        description="ID категории, к которой относится продукт",
        example=1,
    )
    tag_ids: List[int] = Field(
        [],
        description="Список ID тегов, связанных с продуктом",
        example=[101, 105],
    )


class ProductUpdate(ProductCreate):
    """
    Схема для полного обновления продукта (метод PUT).
    Все поля обязательны, как при создании.
    """

    id: int = Field(..., description="ID продукта, который нужно обновить", example=42)


class Product(BaseModel):
    """Схема для отображения продукта со всеми связанными данными из БД."""

    id: int = Field(..., description="Уникальный идентификатор продукта", example=42)
    name: str = Field(
        ...,
        description="Название продукта",
        example="Смартфон 'Космос-X'",
    )
    description: Optional[str] = Field(
        None,
        description="Подробное описание продукта",
        example="Футуристический смартфон с прозрачным экраном и ИИ-помощником.",
    )
    image_url: Optional[str] = Field(
        None,
        description="URL-адрес изображения продукта",
        example="https://example.com/images/kosmos-x.jpg",
    )
    price_shmeckles: float = Field(
        ...,
        description="Цена продукта в Шмеклях",
        example=999.99,
    )
    price_flurbos: float = Field(
        ...,
        description="Цена продукта в Флёрбосах",
        example=120.50,
    )
    category: Optional[Category] = Field(
        None,
        description="Категория продукта (вложенный объект)",
    )
    tags: List[Tag] = Field(
        [],
        description="Список тегов продукта (вложенные объекты)",
    )

    model_config = ConfigDict(from_attributes=True)
