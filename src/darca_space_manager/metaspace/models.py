from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator

class Space(BaseModel):
    name: str
    label: Optional[str] = None
    repository: str
    created_at: datetime
    last_modified_at: datetime
    owner: Optional[str] = None
    permissions: Optional[List[str]] = None

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

class SpaceURI(BaseModel):
    space: str
    path: str

    @classmethod
    def from_str(cls, uri: str) -> "SpaceURI":
        if not uri.startswith("space://"):
            raise ValueError(f"Invalid URI scheme: {uri}")
        parts = uri[len("space://"):].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid space URI format: {uri}")
        return cls(space=parts[0], path=parts[1])

    def __str__(self) -> str:
        return f"space://{self.space}/{self.path}"

    @property
    def space_name(self) -> str:
        return self.space

    @property
    def relative_path(self) -> str:
        return self.path