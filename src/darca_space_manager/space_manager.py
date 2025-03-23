"""
space_manager.py

A local storage abstraction layer for managing logical spaces.
Supports space creation, deletion, listing, and metadata tracking.

This implementation uses the local filesystem and YAML metadata files.
"""

import datetime
import os
from typing import List

from darca_exception.exception import DarcaException
from darca_file_utils.directory_utils import DirectoryUtils
from darca_file_utils.file_utils import FileUtils
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils

from darca_space_manager import config

# Initialize logger
logger = DarcaLogger(name="space_manager").get_logger()


class SpaceManagerException(DarcaException):
    """Custom exception for errors in the SpaceManager."""

    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "SPACE_MANAGER_ERROR",
            metadata=metadata,
            cause=cause,
        )


class SpaceManager:
    """
    Manages logical storage spaces and their metadata using local filesystem.
    """

    def __init__(self):
        self.space_dir = config.DIRECTORIES["SPACE_DIR"]
        self.metadata_dir = config.DIRECTORIES["METADATA_DIR"]

    def _get_space_path(self, name: str) -> str:
        return os.path.join(self.space_dir, name)

    def _get_metadata_path(self, name: str) -> str:
        return os.path.join(self.metadata_dir, f"{name}.yaml")

    def space_exists(self, name: str) -> bool:
        """
        Check if a space exists by name.

        Args:
            name (str): Name of the space.

        Returns:
            bool: True if space exists.
        """
        exists = DirectoryUtils.directory_exist(self._get_space_path(name))
        logger.debug(f"Checked if space '{name}' exists: {exists}")
        return exists

    def list_spaces(self) -> List[str]:
        """
        List all allocated spaces.

        Returns:
            List[str]: Names of all existing spaces.
        """
        logger.debug("Listing all allocated spaces.")
        try:
            return DirectoryUtils.list_directory(self.space_dir)
        except Exception as e:
            raise SpaceManagerException(
                message="Failed to list spaces.",
                error_code="LIST_SPACES_FAILED",
                cause=e,
            )

    def count_spaces(self) -> int:
        """
        Get the number of allocated spaces.

        Returns:
            int: Count of spaces.
        """
        count = len(self.list_spaces())
        logger.debug(f"Total spaces allocated: {count}")
        return count

    def _generate_metadata(self, name: str) -> dict:
        """
        Generate metadata for a new space.

        Args:
            name (str): Name of the space.

        Returns:
            dict: Metadata dictionary.
        """
        metadata = {
            "type": "local",
            "path": self._get_space_path(name),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
        }
        logger.debug(f"Generated metadata for space '{name}': {metadata}")
        return metadata

    def create_space(self, name: str) -> bool:
        """
        Allocate a new space and store internal metadata.

        Args:
            name (str): Name of the space.

        Returns:
            bool: True if space created successfully.

        Raises:
            SpaceManagerException: If space already exists or creation fails.
        """
        logger.debug(f"Creating space '{name}'.")

        if self.space_exists(name):
            raise SpaceManagerException(
                message=f"Space '{name}' already exists.",
                error_code="SPACE_ALREADY_EXISTS",
                metadata={"space": name},
            )

        try:
            DirectoryUtils.create_directory(self._get_space_path(name))
        except Exception as e:
            raise SpaceManagerException(
                message=f"Failed to create space '{name}'.",
                error_code="CREATE_SPACE_FAILED",
                metadata={"space": name},
                cause=e,
            )

        metadata = self._generate_metadata(name)

        try:
            YamlUtils.save_yaml_file(
                file_path=self._get_metadata_path(name),
                data=metadata,
                validate=False,
            )
        except Exception as e:
            # Rollback directory creation
            DirectoryUtils.remove_directory(self._get_space_path(name))
            raise SpaceManagerException(
                message=f"Failed to store metadata for space '{name}'.",
                error_code="METADATA_WRITE_FAILED",
                metadata={"space": name},
                cause=e,
            )

        logger.info(f"Space '{name}' successfully created.")
        return True

    def get_space_metadata(self, name: str) -> dict:
        """
        Retrieve metadata associated with a space.

        Args:
            name (str): Name of the space.

        Returns:
            dict: Metadata dictionary.

        Raises:
            SpaceManagerException: If metadata cannot be loaded.
        """
        logger.debug(f"Retrieving metadata for space '{name}'.")

        if not self.space_exists(name):
            raise SpaceManagerException(
                message=f"Space '{name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        try:
            return YamlUtils.load_yaml_file(self._get_metadata_path(name))
        except Exception as e:
            raise SpaceManagerException(
                message=f"Failed to load metadata for space '{name}'.",
                error_code="METADATA_READ_FAILED",
                metadata={"space": name},
                cause=e,
            )

    def delete_space(self, name: str) -> bool:
        """
        Delete a space and its metadata.

        Args:
            name (str): Name of the space.

        Returns:
            bool: True if deletion succeeded.

        Raises:
            SpaceManagerException: If space or metadata deletion fails.
        """
        logger.debug(f"Deleting space '{name}' and its metadata.")

        if not self.space_exists(name):
            raise SpaceManagerException(
                message=f"Cannot delete non-existent space '{name}'.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        try:
            DirectoryUtils.remove_directory(self._get_space_path(name))
        except Exception as e:
            raise SpaceManagerException(
                message=f"Failed to delete space directory '{name}'.",
                error_code="SPACE_DELETE_FAILED",
                metadata={"space": name},
                cause=e,
            )

        metadata_path = self._get_metadata_path(name)
        if FileUtils.file_exist(metadata_path):
            try:
                FileUtils.remove_file(metadata_path)
            except Exception as e:
                raise SpaceManagerException(
                    message=f"Failed to delete metadata for space '{name}'.",
                    error_code="METADATA_DELETE_FAILED",
                    metadata={"space": name},
                    cause=e,
                )

        logger.info(f"Space '{name}' successfully deleted.")
        return True
