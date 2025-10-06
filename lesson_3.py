from pydantic import BaseModel, Field



class CreateProduct(BaseModel):
    """
    Модель для операций POST, PUT
    """
    name: str = Field(..., example="Позалоченный Плюмбус", description="Название товара")
    description: str = Field(
        ..., example="Описание товара", description="Подробное описание товара"
    )
    prices: dict = Field(
        ...,
        example={"shmeckles": 6.5, "credits": 4.8, "flurbos": 3.2},
        description="Цены в разных валютах",
    )
    image_url: str = Field(
        ..., example="/images/plumbus.webp", description="URL изображения товара"
    )

class Product(CreateProduct):
    """
    Модель для операций GET
    """
    id: int = Field(..., example=1, description="Уникальный идентификатор товара")