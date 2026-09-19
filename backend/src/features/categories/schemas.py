import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_archived: bool
    created_at: datetime
