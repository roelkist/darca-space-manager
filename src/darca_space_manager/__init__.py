"""
darca_space_manager

Logical space management framework for filesystem-based environments.
Provides structured subspace creation, file operations, command execution,
and metadata integrity with safe concurrency features.
"""

from darca_space_manager.api.space_service import SpaceService

__all__ = [
    "SpaceService",
    "Space",
    "SpaceURI",
]
