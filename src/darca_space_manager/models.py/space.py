"""
models/space.py

Defines the Space metadata model.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class Space(BaseModel):
    """
    Represents metadata about a logical space.
    """

    name: str = Field(..., description="Unique space name")
    path: str = Field(..., description="Filesystem path to space root")
    label: Optional[str] = Field("", description="Optional space label")
    parent: Optional[str] = Field(None, description="Parent space name, if nested")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    last_modified_at: Optional[datetime] = Field(None, description="Last modified timestamp (UTC)")

    @validator("name")
    def validate_name(cls, v: str) -> str:
        if "/" in v or "\\" in v:
            raise ValueError("Space name cannot contain slashes ('/' or '\\').")
        if not v.strip():
            raise ValueError("Space name cannot be empty or whitespace.")
        return v

    @classmethod
    def from_dict(cls, data: dict) -> "Space":
        return cls(**data)

    def to_dict(self) -> dict:
        return self.dict()
