"""
space_manager.py

Manages logical storage spaces using the local filesystem.
Supports hierarchical space creation, deletion, metadata tracking, and
recursive discovery.

FIXME Mapping of space names to paths is not yet implemented.
Create sub space fails
FIXME Don't remove spaces that have child spaces. Force option.
FIXME Add a way to rename spaces.
FIXME Add a way to move spaces.
"""

import datetime
import os
from typing import Dict, List, Union

from darca_exception.exception import DarcaException
from darca_file_utils.directory_utils import (
    DirectoryUtils,
    DirectoryUtilsException,
)
from darca_file_utils.file_utils import FileUtils
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils

from darca_space_manager import config

logger = DarcaLogger(name="space_manager").get_logger()

METADATA_FILENAME = "metadata.yaml"


class SpaceManagerException(DarcaException):
    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "SPACE_MANAGER_ERROR",
            metadata=metadata,
            cause=cause,
        )


class SpaceManager:
    def __init__(self):
        config.ensure_directories_exist()
        dirs = config.get_directories()
        self.space_dir = dirs["SPACE_DIR"]
        self.index = self._load_index()
        self.refresh_index()
        logger.info("✅ SpaceManager initialized and index refreshed.")

    def _load_index(self) -> Dict:
        try:
            index_file = os.path.join(
                config.get_directories()["METADATA_DIR"], "spaces_index.yaml"
            )
            if not FileUtils.file_exist(index_file):
                logger.info("ℹ️ Index file not found. Initializing new index.")
                return {"spaces": []}
            logger.debug("🔍 Loading index file.")
            return YamlUtils.load_yaml_file(index_file)
        except Exception as e:
            logger.error("❌ Failed to load index file.", exc_info=True)
            raise SpaceManagerException(
                "Failed to load spaces index.",
                error_code="INDEX_LOAD_FAILED",
                cause=e,
            )

    def _save_index(self):
        try:
            index_file = os.path.join(
                config.get_directories()["METADATA_DIR"], "spaces_index.yaml"
            )
            YamlUtils.save_yaml_file(index_file, self.index)
            logger.debug("💾 Index successfully saved.")
        except Exception as e:
            logger.error("❌ Failed to save index.", exc_info=True)
            raise SpaceManagerException(
                "Failed to save spaces index.",
                error_code="INDEX_SAVE_FAILED",
                cause=e,
            )

    def _generate_metadata(self, name: str, label: str, path: str) -> dict:
        return {
            "name": name,
            "label": label,
            "path": path,
            "created_at": datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat(),
            "subspaces": [],
        }

    def _scan_directory(self, directory: str) -> List[dict]:
        """Scan using DirectoryUtils for all metadata.yaml files."""
        discovered = []

        try:
            all_files = DirectoryUtils.list_directory(
                directory, recursive=True
            )
            metadata_files = [
                f
                for f in all_files
                if os.path.basename(f) == METADATA_FILENAME
            ]

            for rel_path in metadata_files:
                full_path = os.path.join(directory, rel_path)
                try:
                    metadata = YamlUtils.load_yaml_file(full_path)
                    if all(
                        k in metadata
                        for k in ["name", "label", "path", "created_at"]
                    ):
                        discovered.append(metadata)
                        logger.debug(
                            f"🔎 Discovered valid space: {metadata['name']} at "
                            f"{metadata['path']}"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Incomplete metadata in {full_path}, skipping."
                        )
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to load metadata in {full_path}: {e}"
                    )
        except DirectoryUtilsException as e:
            raise SpaceManagerException(
                "Failed to scan directory.",
                error_code="DIRECTORY_SCAN_FAILED",
                cause=e,
            )
        except Exception as e:
            raise SpaceManagerException(
                "Unexpected error during directory scan.", cause=e
            )

        return discovered

    def _get_space_path(self, name: str) -> str:
        """
        Internal helper to resolve the absolute path of a space by name.
        """
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                message=f"Space '{name}' not found.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )
        return space["path"]

    def refresh_index(self):
        logger.info("🔄 Refreshing space index via recursive discovery.")
        self.index["spaces"] = self._scan_directory(self.space_dir)
        self._save_index()

    def space_exists(self, name: str) -> bool:
        exists = any(space["name"] == name for space in self.index["spaces"])
        logger.debug(f"✅ Space exists check for '{name}': {exists}")
        return exists

    def get_space(self, name: str) -> Union[dict, None]:
        try:
            return next(
                (s for s in self.index["spaces"] if s["name"] == name), None
            )
        except Exception as e:
            logger.error(f"❌ Failed to get space '{name}'.", exc_info=True)
            raise SpaceManagerException(
                "Failed to retrieve space.", metadata={"space": name}, cause=e
            )

    def create_space(
        self, name: str, label: str = "", parent_path: str = None
    ) -> bool:
        """
        Create a new space. Supports nested structure like 'space1/subdir'.

        Args:
            name (str): The name of the new space (must be unique).
            label (str): A label for filtering/categorization.
            parent_path (str): A path like 'space1/subdir', where the first
            part must be an existing space.

        Returns:
            bool: True if the space was created successfully.
        """
        if self.space_exists(name):
            raise SpaceManagerException(
                f"Space '{name}' already exists.",
                metadata={"space": name},
            )

        try:
            # Determine base space and optional subpath
            if parent_path:
                parts = parent_path.strip("/").split("/")
                base_space_name = parts[0]
                relative_subpath = (
                    os.path.join(*parts[1:]) if len(parts) > 1 else ""
                )

                base_space = self.get_space(base_space_name)
                if not base_space:
                    raise SpaceManagerException(
                        f"Base space '{base_space_name}' not found in "
                        f"path '{parent_path}'.",
                        error_code="BASE_SPACE_NOT_FOUND",
                        metadata={
                            "base": base_space_name,
                            "path": parent_path,
                        },
                    )

                # Final space path = base + relative path + new space name
                base_path = base_space["path"]
                destination_path = os.path.normpath(
                    os.path.join(base_path, relative_subpath, name)
                )

                # Ensure the new path is within the base space
                if not destination_path.startswith(base_path):
                    raise SpaceManagerException(
                        "Target path escapes base space boundaries.",
                        error_code="PATH_ESCAPE_DETECTED",
                        metadata={
                            "base": base_space_name,
                            "resolved_path": destination_path,
                        },
                    )

                # Create intermediate folders if necessary
                DirectoryUtils.create_directory(
                    os.path.dirname(destination_path)
                )
            else:
                # No parent path; create directly under root space directory
                destination_path = os.path.join(self.space_dir, name)

            # Create the actual space directory
            DirectoryUtils.create_directory(destination_path)

            # Write metadata
            metadata = self._generate_metadata(
                name=name, label=label, path=destination_path
            )
            metadata_path = os.path.join(destination_path, METADATA_FILENAME)
            YamlUtils.save_yaml_file(metadata_path, metadata)

            # Refresh index
            self.refresh_index()

            logger.info(
                f"✅ Space '{name}' created at '{destination_path}' "
                f"with label '{label}'."
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create space '{name}' under '{parent_path}'.",
                exc_info=True,
            )
            raise SpaceManagerException(
                message=(
                    f"Failed to create space '{name}' under '{parent_path}'."
                ),
                error_code="CREATE_SPACE_FAILED",
                metadata={"space": name, "parent_path": parent_path},
                cause=e,
            )

    def delete_space(self, name: str) -> bool:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' not found.", metadata={"space": name}
            )

        try:
            DirectoryUtils.remove_directory(space["path"])
            self.refresh_index()
            logger.info(f"🗑️ Space '{name}' deleted.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete space '{name}'.", exc_info=True)
            raise SpaceManagerException(
                f"Failed to delete space '{name}'.",
                metadata={"space": name},
                cause=e,
            )

    def list_spaces(self, label_filter: str = None) -> List[dict]:
        try:
            logger.debug(f"📃 Listing spaces (filter: {label_filter})")
            return (
                [
                    s
                    for s in self.index["spaces"]
                    if s.get("label") == label_filter
                ]
                if label_filter
                else self.index["spaces"]
            )
        except Exception as e:
            logger.error("❌ Failed to list spaces.", exc_info=True)
            raise SpaceManagerException(
                "Failed to list spaces.",
                error_code="LIST_SPACES_FAILED",
                cause=e,
            )

    def create_directory(self, space_name: str, relative_path: str) -> str:
        space = self.get_space(space_name)
        if not space:
            raise SpaceManagerException(
                "Space not found for directory creation.",
                metadata={"space": space_name},
            )

        abs_path = os.path.normpath(os.path.join(space["path"], relative_path))
        if not abs_path.startswith(space["path"]):
            raise SpaceManagerException(
                "Directory path escapes space boundaries.",
                metadata={"space": space_name},
            )

        try:
            DirectoryUtils.create_directory(abs_path)
            logger.info(
                f"📁 Created directory '{relative_path}'"
                f" in space '{space_name}'."
            )
            return abs_path
        except Exception as e:
            logger.error(
                f"❌ Failed to create directory in space '{space_name}'.",
                exc_info=True,
            )
            raise SpaceManagerException(
                "Failed to create directory.",
                metadata={"space": space_name, "path": relative_path},
                cause=e,
            )

    def remove_directory(self, space_name: str, relative_path: str) -> bool:
        space = self.get_space(space_name)
        if not space:
            raise SpaceManagerException(
                "Space not found for directory removal.",
                metadata={"space": space_name},
            )

        abs_path = os.path.normpath(os.path.join(space["path"], relative_path))
        if not abs_path.startswith(space["path"]):
            raise SpaceManagerException(
                "Directory path escapes space boundaries.",
                metadata={"space": space_name},
            )

        try:
            DirectoryUtils.remove_directory(abs_path)
            logger.info(
                f"🗑️ Removed directory '{relative_path}' "
                f"in space '{space_name}'."
            )
            return True
        except Exception as e:
            logger.error(
                f"❌ Failed to remove directory in space '{space_name}'.",
                exc_info=True,
            )
            raise SpaceManagerException(
                "Failed to remove directory.",
                metadata={"space": space_name, "path": relative_path},
                cause=e,
            )

    def get_directory_last_modified(
        self, name: str, directory: str = None
    ) -> float:
        """
        Return the 'last modified' timestamp of a space (directory), in seconds
        since the Unix epoch (UTC). The directory's timestamp is the newest
        (i.e., highest mtime) among all files it contains, recursively.
        If no files exist, we fall back to the directory's own mtime.

        Args:
            name (str): The name of the space.

        Returns:
            float: The highest file modification timestamp (UTC) in the space,
                   or the directory's own timestamp if no files are found.
        """
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                message=f"Space '{name}' not found.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        try:
            # Determine the target directory (base space or subdirectory)
            base_path = space["path"]
            if directory:
                target_path = os.path.normpath(
                    os.path.join(base_path, directory)
                )
                # Ensure the new path is within the base space
                if os.path.commonpath(
                    [base_path, target_path]
                ) != os.path.commonpath([base_path]):
                    raise SpaceManagerException(
                        message="Subdirectory path escapes space boundaries.",
                        error_code="PATH_ESCAPE_DETECTED",
                        metadata={
                            "space": name,
                            "requested_subdir": directory,
                        },
                    )
            else:
                target_path = base_path
            # Recursively list all entries (files + subdirectories)
            # within the space.
            all_entries = DirectoryUtils.list_directory(
                space["path"], recursive=True
            )

            # If no entries at all, just return the directory's own
            # modification time.
            if not all_entries:
                return os.path.getmtime(space["path"])

            latest_timestamp = 0.0
            for entry in all_entries:
                full_path = os.path.join(space["path"], entry)

                # We only consider files, not subdirectories.
                if os.path.isfile(full_path):
                    file_mtime = os.path.getmtime(full_path)
                    if file_mtime > latest_timestamp:
                        latest_timestamp = file_mtime

            # If no files were found at all (all_entries might have
            # been directories),
            # again fall back to the directory's own mtime.
            if latest_timestamp == 0.0:
                return os.path.getmtime(space["path"])

            return latest_timestamp

        except Exception as e:
            logger.error(
                f"Failed to compute last modified time for space '{name}'.",
                exc_info=True,
            )
            raise SpaceManagerException(
                message=(
                    f"Error retrieving 'last modified' timestamp "
                    f"for space '{name}'."
                ),
                error_code="SPACE_DIR_MTIME_FAILED",
                metadata={"space": name},
                cause=e,
            )
