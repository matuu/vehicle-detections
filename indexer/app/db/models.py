from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class VehicleDetectionModel(BaseModel):
    """
    This model capture data for vehicle event detection.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    year: int = Field(alias="Year")
    make: str = Field(alias="Make")
    model: str = Field(alias="Model")
    category: str = Field(alias="Category")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "Year": 2008,
                "Make": "Jeep",
                "Model": "Wrangler",
                "Category": "SUV"
            }
        }

    def to_alert(self) -> dict:
        return dict(
            year=self.year,
            make=self.make,
            model=self.model,
            category=self.category,
            created_at=self.created_at.isoformat()
        )