# space_path_service.py
# License: MIT

import os
from typing import Optional


class SpacePathService:
    """
    Resolves and validates paths inside spaces.

    Prevents path traversal and ensures logical containment.
    """

    def resolve_path(self, base_path: str, relative_path: Optional[str] = None) -> str:
        """
        Resolve a relative path within a space to an absolute path.

        Raises:
            ValueError if resolved path escapes the base.
        """
        if relative_path:
            combined = os.path.join(base_path, relative_path)
        else:
            combined = base_path

        resolved = os.path.normpath(combined)
        self.ensure_within_space(base_path, resolved)
        return resolved

    def ensure_within_space(self, base_path: str, target_path: str):
        """
        Enforce that `target_path` stays within `base_path`.

        Raises:
            ValueError if path escapes.
        """
        base_real = os.path.realpath(base_path)
        target_real = os.path.realpath(target_path)

        if os.path.commonpath([base_real, target_real]) != base_real:
            raise ValueError(f"Path '{target_path}' escapes space boundary '{base_path}'")
