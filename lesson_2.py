# Lesson 2


from pydantic import BaseModel
from typing import Dict

class Product(BaseModel):
    id: int
    name: str
    description: str
    prices: Dict[str, float]
    image_url: str
