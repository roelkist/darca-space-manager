import os
from typing import Optional

class SpacePathManager:
    """
    Helper for resolving and validating paths inside spaces.
    """

    def resolve_path(self, base_path: str, relative_path: Optional[str] = None) -> str:
        if relative_path:
            combined_path = os.path.join(base_path, relative_path)
        else:
            combined_path = base_path

        resolved_path = os.path.normpath(combined_path)

        self.ensure_within_space(base_path, resolved_path)

        return resolved_path

    def ensure_within_space(self, base_path: str, target_path: str):
        """
        Raise ValueError if target_path escapes base_path.
        """

        # Normalize and compare common paths
        base_real = os.path.realpath(base_path)
        target_real = os.path.realpath(target_path)

        if os.path.commonpath([base_real, target_real]) != base_real:
            raise ValueError(f"Path '{target_path}' escapes space boundary '{base_path}'")
