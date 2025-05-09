from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class Space(BaseModel):
    name: str
    path: str
    label: Optional[str] = None
    parent: Optional[str] = None
    created_at: datetime
    last_modified_at: datetime

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("Space name must be a non-empty string without slashes.")
        return value

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Space":
        return cls(**data)

    def __str__(self) -> str:
        return f"Space(name={self.name}, path={self.path})"
