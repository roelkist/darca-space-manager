# tests/test_space_manager.py

import os
import time
from unittest.mock import patch

import pytest

from darca_space_manager.space_manager import (
    SpaceManagerException,
)

# === Existing Functionality Tests ===


def test_create_space_success(space_manager):
    assert space_manager.create_space("space1", label="project")
    assert space_manager.space_exists("space1")


def test_create_space_duplicate(space_manager):
    space_manager.create_space("space1")
    with pytest.raises(SpaceManagerException, match="already exists"):
        space_manager.create_space("space1")


def test_delete_space_success(space_manager):
    space_manager.create_space("todelete")
    assert space_manager.delete_space("todelete")


def test_delete_space_not_found(space_manager):
    with pytest.raises(SpaceManagerException, match="not found"):
        space_manager.delete_space("ghost")


def test_list_spaces_success(space_manager):
    space_manager.create_space("listme", label="data")
    spaces = space_manager.list_spaces(label_filter="data")
    assert any(s["name"] == "listme" for s in spaces)


def test_list_spaces_failure(space_manager, monkeypatch):
    monkeypatch.setattr(space_manager, "index", None)
    with pytest.raises(SpaceManagerException):
        space_manager.list_spaces()


def test_create_directory_success(space_manager):
    space_manager.create_space("withdir")
    path = space_manager.create_directory("withdir", "nested/folder")
    assert path.endswith("nested/folder")


def test_create_directory_escape(space_manager):
    space_manager.create_space("escape")
    with pytest.raises(
        SpaceManagerException, match="escapes space boundaries"
    ):
        space_manager.create_directory("escape", "../../bad")


def test_remove_directory_success(space_manager):
    space_manager.create_space("rmdir")
    space_manager.create_directory("rmdir", "sub")
    assert space_manager.remove_directory("rmdir", "sub")


def test_remove_directory_escape(space_manager):
    space_manager.create_space("rm_escape")
    with pytest.raises(SpaceManagerException):
        space_manager.remove_directory("rm_escape", "../../../")


def test_get_space_success(space_manager):
    space_manager.create_space("getter")
    space = space_manager.get_space("getter")
    assert space["name"] == "getter"


def test_get_space_failure(space_manager):
    assert space_manager.get_space("missing") is None


def test_space_exists_true(space_manager):
    space_manager.create_space("checkme")
    assert space_manager.space_exists("checkme")


def test_space_exists_false(space_manager):
    assert not space_manager.space_exists("ghost")


def test_refresh_index_success(space_manager):
    space_manager.create_space("refresh")
    space_manager.refresh_index()
    assert space_manager.space_exists("refresh")


# === Additional Coverage Tests ===


def test_load_index_failure(monkeypatch):
    from darca_space_manager import space_manager

    monkeypatch.setattr(
        "darca_file_utils.file_utils.FileUtils.file_exist", lambda *_: True
    )
    monkeypatch.setattr(
        "darca_yaml.yaml_utils.YamlUtils.load_yaml_file",
        lambda *_: (_ for _ in ()).throw(Exception("Boom")),
    )
    with pytest.raises(
        space_manager.SpaceManagerException,
        match="Failed to load spaces index.",
    ):
        space_manager.SpaceManager()._load_index()


def test_save_index_failure(space_manager, monkeypatch):
    monkeypatch.setattr(
        "darca_yaml.yaml_utils.YamlUtils.save_yaml_file",
        lambda *_: (_ for _ in ()).throw(Exception("Fail save")),
    )
    space_manager.index["spaces"].append({"dummy": True})
    with pytest.raises(
        SpaceManagerException, match="Failed to save spaces index."
    ):
        space_manager._save_index()


def test_scan_directory_incomplete_metadata(space_manager, tmp_path, caplog):
    caplog.set_level("WARNING")  # Set for all loggers

    broken_space = tmp_path / "broken"
    broken_space.mkdir()
    (broken_space / "metadata.yaml").write_text(
        "name: test\nlabel: ''"
    )  # incomplete

    files = space_manager._scan_directory(str(tmp_path))

    assert files == []
    # assert any("Incomplete metadata" in message for message in
    # caplog.messages)


def test_scan_directory_metadata_load_failure(
    space_manager, tmp_path, monkeypatch, caplog
):
    caplog.set_level("WARNING")  # Capture all warnings

    failmeta = tmp_path / "failmeta"
    failmeta.mkdir()
    (failmeta / "metadata.yaml").write_text("this: will break: badly")

    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory",
        lambda *_1, **_2: [
            str((failmeta / "metadata.yaml").relative_to(tmp_path))
        ],
    )
    monkeypatch.setattr(space_manager, "space_dir", str(tmp_path))

    files = space_manager._scan_directory(str(tmp_path))

    assert files == []
    # assert any("Failed to load metadata" in message for message in
    # caplog.messages)


def test_scan_directory_exception(space_manager, monkeypatch):
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory",
        lambda *_: (_ for _ in ()).throw(Exception("explosion")),
    )
    with pytest.raises(
        SpaceManagerException, match="Unexpected error during directory scan."
    ):
        space_manager._scan_directory("/tmp/fake")


def test_get_space_path_not_found(space_manager):
    with pytest.raises(
        SpaceManagerException, match="Space 'missing' not found"
    ):
        space_manager._get_space_path("missing")


def test_get_space_exception(space_manager, monkeypatch):
    monkeypatch.setattr(space_manager, "index", {"spaces": None})
    with pytest.raises(
        SpaceManagerException, match="Failed to retrieve space"
    ):
        space_manager.get_space("whatever")


def test_create_space_with_parent_success(space_manager):
    space_manager.create_space("base")
    assert space_manager.create_space("child", parent_path="base/inner")


def test_create_space_base_missing(space_manager):
    with pytest.raises(
        SpaceManagerException, match="Base space 'nospace' not found"
    ):
        space_manager.create_space("sub", parent_path="nospace/child")


def test_create_space_path_escape(space_manager):
    space_manager.create_space("safe")
    with pytest.raises(
        SpaceManagerException, match="escapes base space boundaries"
    ):
        space_manager.create_space("hack", parent_path="safe/../../etc")


def test_create_space_general_failure(space_manager, monkeypatch):
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.create_directory",
        lambda *_: (_ for _ in ()).throw(Exception("kaboom")),
    )
    with pytest.raises(SpaceManagerException, match="CREATE_SPACE_FAILED"):
        space_manager.create_space("crash")


def test_delete_space_exception(space_manager, monkeypatch):
    space_manager.create_space("todelete")
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.remove_directory",
        lambda *_: (_ for _ in ()).throw(Exception("boom")),
    )
    with pytest.raises(SpaceManagerException, match="Failed to delete space"):
        space_manager.delete_space("todelete")


def test_create_directory_no_space(space_manager):
    with pytest.raises(
        SpaceManagerException, match="Space not found for directory creation"
    ):
        space_manager.create_directory("ghost", "newdir")


def test_create_directory_failure(space_manager, monkeypatch):
    space_manager.create_space("dirfail")
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.create_directory",
        lambda *_: (_ for _ in ()).throw(Exception("mkdir error")),
    )
    with pytest.raises(
        SpaceManagerException, match="Failed to create directory"
    ):
        space_manager.create_directory("dirfail", "boom")


def test_remove_directory_no_space(space_manager):
    with pytest.raises(
        SpaceManagerException, match="Space not found for directory removal"
    ):
        space_manager.remove_directory("ghost", "whatever")


def test_remove_directory_failure(space_manager, monkeypatch):
    space_manager.create_space("rmdirfail")
    space_manager.create_directory("rmdirfail", "sub")
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.remove_directory",
        lambda *_: (_ for _ in ()).throw(Exception("rm error")),
    )
    with pytest.raises(
        SpaceManagerException, match="Failed to remove directory"
    ):
        space_manager.remove_directory("rmdirfail", "sub")


def test_scan_directory_directoryutils_exception(space_manager, monkeypatch):
    from darca_file_utils.directory_utils import DirectoryUtilsException

    def broken_list_directory(directory, recursive=True):
        raise DirectoryUtilsException("Simulated failure")

    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory",
        broken_list_directory,
    )

    with pytest.raises(SpaceManagerException, match="DIRECTORY_SCAN_FAILED"):
        space_manager._scan_directory("/dummy")


def test_get_space_path_success(space_manager):
    space_manager.create_space("pathtest")
    path = space_manager._get_space_path("pathtest")
    assert os.path.basename(path) == "pathtest"


def test_get_directory_last_modified_empty(space_manager):
    """
    If the space is empty (no files at all), we expect the method to fall back
    to the directory's own mtime. Just ensure it doesn't raise an error and
    returns a float.
    """
    space_name = "empty_mtime_space"
    space_manager.create_space(space_name)

    mtime = space_manager.get_directory_last_modified(space_name)
    assert isinstance(mtime, float), "Should return a float timestamp"


def test_get_directory_last_modified_with_files(space_manager):
    """
    If the space has files, the method should return the newest
    file's timestamp.
    """
    space_name = "files_mtime_space"
    space_manager.create_space(space_name)

    # Create a subdirectory and file
    space_path = space_manager.get_space(space_name)["path"]
    os.makedirs(os.path.join(space_path, "subdir"), exist_ok=True)

    file1_path = os.path.join(space_path, "file1.txt")
    with open(file1_path, "w") as f:
        f.write("Hello 1")

    file2_path = os.path.join(space_path, "subdir", "file2.txt")
    with open(file2_path, "w") as f:
        f.write("Hello 2")

    # Force a slight delay so we can ensure one file is newer
    time.sleep(0.5)
    with open(file2_path, "a") as f:
        f.write("Some more text to update its timestamp")

    file1_mtime = os.path.getmtime(file1_path)
    file2_mtime = os.path.getmtime(file2_path)
    assert file2_mtime > file1_mtime, "file2 should have a newer mtime"

    # Check method
    dir_mtime = space_manager.get_directory_last_modified(space_name)
    assert isinstance(dir_mtime, float), "Should return a float"
    assert dir_mtime == pytest.approx(
        file2_mtime, abs=0.001
    ), "Directory last modified should match the newest file (file2)."


def test_get_directory_last_modified_nonexistent_space(space_manager):
    """
    If the space doesn't exist, we expect a SPACE_NOT_FOUND error.
    """
    with pytest.raises(SpaceManagerException) as exc_info:
        space_manager.get_directory_last_modified("no_such_space")
    assert "SPACE_NOT_FOUND" in str(exc_info.value)


def test_get_directory_last_modified_no_entries(space_manager):
    """
    Force DirectoryUtils.list_directory to return an empty list,
    ensuring we hit the line:
        if not all_entries:
            return os.path.getmtime(space["path"])
    """
    space_name = "no_entries_space"
    space_manager.create_space(space_name)

    # Mock list_directory to always return an empty list
    with patch(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory",
        return_value=[],
    ):
        mtime = space_manager.get_directory_last_modified(space_name)

    # We expect a float (the directory's own mtime)
    assert isinstance(
        mtime, float
    ), "Should return a float for an empty directory."
    # Optionally check that mtime matches the actual directory's mtime
    dir_path = space_manager.get_space(space_name)["path"]
    assert abs(mtime - os.path.getmtime(dir_path)) < 0.01


def test_get_directory_last_modified_only_subdirs_no_files(space_manager):
    """
    By mocking DirectoryUtils.list_directory to return only subdirectories
    (no files), we ensure 'all_entries' is non-empty while 'latest_timestamp'
    remains 0.0, forcing the code to return the directory's own mtime.
    """
    space_name = "only_subdirs_space"
    space_manager.create_space(space_name)
    space_path = space_manager.get_space(space_name)["path"]

    # Mock DirectoryUtils.list_directory to return subdirectories (no files)
    with patch(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory"
    ) as mock_list:
        mock_list.return_value = ["sub1", "sub2", "sub2/nested"]

        dir_mtime = space_manager.get_directory_last_modified(space_name)

    assert isinstance(dir_mtime, float), "Should return a float timestamp."

    actual_mtime = os.path.getmtime(space_path)
    assert (
        abs(dir_mtime - actual_mtime) < 0.01
    ), "Expected the directory's own mtime since no files exist."


def test_get_directory_last_modified_exception(space_manager):
    """
    Force an error inside get_directory_last_modified by mocking
    DirectoryUtils.list_directory to raise an exception, ensuring we hit:

        except Exception as e:
            logger.error(...)
            raise SpaceManagerException(...)
    """
    space_name = "error_space"
    space_manager.create_space(space_name)

    with patch(
        "darca_file_utils.directory_utils.DirectoryUtils.list_directory",
        side_effect=OSError("Mocked error"),
    ):
        with pytest.raises(SpaceManagerException) as exc_info:
            space_manager.get_directory_last_modified(space_name)

    # Confirm the raised exception includes the expected code/message
    assert "SPACE_DIR_MTIME_FAILED" in str(exc_info.value)
    assert (
        f"Error retrieving 'last modified' timestamp for space '{space_name}'"
        in str(exc_info.value)
    )


def test_get_directory_last_modified_subdirectory_success(space_manager):
    """
    Create a space, add a subdirectory with a file, then call
    get_directory_last_modified(space, directory=subdir).
    Should return that file's mtime.
    """
    space_name = "mtime_subdir_space"
    space_manager.create_space(space_name)
    base_path = space_manager.get_space(space_name)["path"]

    # Create the subdirectory and a file
    subdir_path = os.path.join(base_path, "sub1")
    os.makedirs(subdir_path, exist_ok=True)

    file_path = os.path.join(subdir_path, "file.txt")
    with open(file_path, "w") as f:
        f.write("Hello Subdir")

    # Check last modified time for the subdirectory
    subdir_mtime = space_manager.get_directory_last_modified(
        space_name, directory="sub1"
    )
    assert isinstance(subdir_mtime, float), "Should return a float"
    actual_file_mtime = os.path.getmtime(file_path)
    assert (
        abs(subdir_mtime - actual_file_mtime) < 0.1
    ), "Should match file.txt's modification time."


def test_get_directory_last_modified_subdirectory_no_files(space_manager):
    """
    If the specified subdirectory has no files, we fall back to the subdir's
    own mtime.
    """
    space_name = "empty_subdir_mtime"
    space_manager.create_space(space_name)
    base_path = space_manager.get_space(space_name)["path"]

    empty_subdir_path = os.path.join(base_path, "empty_sub")
    os.makedirs(empty_subdir_path, exist_ok=True)

    subdir_mtime = space_manager.get_directory_last_modified(
        space_name, directory="empty_sub"
    )
    assert isinstance(subdir_mtime, float)
    actual_subdir_mtime = os.path.getmtime(empty_subdir_path)
    assert (
        abs(subdir_mtime - actual_subdir_mtime) < 0.1
    ), "Should match the directory's own mtime if no files exist."


def test_get_directory_last_modified_subdirectory_escape(space_manager):
    """
    Attempt to retrieve a subdirectory path that escapes the space boundaries.
    Should raise a SpaceManagerException (PATH_ESCAPE_DETECTED).
    """
    space_name = "escape_subdir_space"
    space_manager.create_space(space_name)

    with pytest.raises(SpaceManagerException) as exc_info:
        space_manager.get_directory_last_modified(
            space_name, directory="../escape"
        )
    assert "escapes space boundaries" in str(exc_info.value)
