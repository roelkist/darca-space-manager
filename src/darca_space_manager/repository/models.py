from typing import Optional, Dict
from pydantic import BaseModel, SecretStr, Field
from enum import Enum
import os


class StorageScheme(str, Enum):
    FILE = "file"
    S3 = "s3"
    MEMORY = "mem"
    # Extend as needed


class Repository(BaseModel):
    name: str
    storage_url: str
    scheme: StorageScheme
    credentials: Optional[Dict[str, SecretStr]] = Field(default=None)
    parameters: Dict[str, str] = Field(default_factory=dict)
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True
    priority: Optional[int] = None

    def get_secret(self, key: str) -> Optional[str]:
        val = self.credentials.get(key) if self.credentials else None
        if isinstance(val, SecretStr):
            raw = val.get_secret_value()
            if raw.startswith("${") and raw.endswith("}"):
                return os.getenv(raw[2:-1])
            return raw
        return None
