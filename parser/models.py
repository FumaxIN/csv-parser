import datetime
import uuid
from pydantic import Field, constr, BaseModel as PydanticBaseModel

from utils.enums import ProcessingStatusEnum


class BaseModel(PydanticBaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    deleted: bool = False

    class Config:
        populate_by_name = True

class CSVupload(BaseModel):
    status: ProcessingStatusEnum = ProcessingStatusEnum.PENDING

class Product(BaseModel):
    name: constr(max_length=100, min_length=1) = Field(...)
    input_image_urls: list[str] = Field(default_factory=list)
    output_image_urls: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Product Name",
                "input_image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "output_image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            }
        }

class ProductInDB(Product, BaseModel):
    associated_csv: CSVupload = Field(...)