from pydantic import BaseModel


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
