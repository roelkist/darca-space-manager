from pydantic import BaseModel
from typing import Optional


class SpaceURI(BaseModel):
    space_name: str
    relative_path: Optional[str] = None

    @classmethod
    def parse(cls, uri: str) -> "SpaceURI":
        if not uri.startswith("space://"):
            raise ValueError("Invalid space URI. Must start with space://")

        path = uri[len("space://"):]
        parts = path.split("/", 1)

        space_name = parts[0]
        relative_path = parts[1] if len(parts) > 1 else None

        return cls(space_name=space_name, relative_path=relative_path)

    def __str__(self):
        if self.relative_path:
            return f"space://{self.space_name}/{self.relative_path}"
        return f"space://{self.space_name}"
