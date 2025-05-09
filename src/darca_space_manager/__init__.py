"""
darca_space_manager

Logical space management framework for filesystem-based environments.
Provides structured subspace creation, file operations, command execution,
and metadata integrity with safe concurrency features.
"""

from darca_space_manager.api.space_service import SpaceService
from darca_space_manager.models.space import Space
from darca_space_manager.models.space_uri import SpaceURI

__all__ = [
    "SpaceService",
    "Space",
    "SpaceURI",
]
