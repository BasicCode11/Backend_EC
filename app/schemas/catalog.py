from pydantic import BaseModel
from typing import List, Optional

from app.schemas.product import ProductResponse
from app.schemas.category import CategoryResponse
from app.schemas.brand import BrandResponse


class CatalogResponse(BaseModel):
    items: List[ProductResponse]
    categories: List[CategoryResponse]
    brands: List[BrandResponse]
    total: int
    page: int
    limit: int
    pages: int
