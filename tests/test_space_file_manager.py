# tests/test_space_file_manager.py
import os
from unittest.mock import patch

import pytest
from darca_file_utils.file_utils import FileUtils, FileUtilsException

from darca_space_manager.space_file_manager import SpaceFileManagerException


def test_file_exists_true(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("testspace")
    sfm.set_file("testspace", "file.txt", "Hello")
    assert sfm.file_exists("testspace", "file.txt")


def test_file_exists_invalid(space_file_manager):
    with pytest.raises(SpaceFileManagerException):
        space_file_manager.file_exists("ghost", "file.txt")


def test_get_file_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("getspace")
    sfm.set_file("getspace", "data.txt", "value")
    content = sfm.get_file("getspace", "data.txt")
    assert "value" in content


def test_get_file_fail(space_file_manager):
    with pytest.raises(SpaceFileManagerException):
        space_file_manager.get_file("ghost", "nofile.txt")


def test_set_file_text_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("write")
    assert sfm.set_file("write", "hello.txt", "Hello")


def test_set_file_unsupported_content(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("badwrite")
    with pytest.raises(SpaceFileManagerException):
        sfm.set_file("badwrite", "bad.bin", 42)


def test_delete_file_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("del")
    sfm.set_file("del", "d.txt", "bye")
    assert sfm.delete_file("del", "d.txt")


def test_delete_file_fail(space_file_manager):
    with pytest.raises(Exception):
        space_file_manager.delete_file("ghost", "fail.txt")


def test_list_files_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("list")
    sfm.set_file("list", "visible.txt", "yes")
    files = sfm.list_files("list")
    assert any("visible.txt" in f for f in files)


def test_list_files_fail(space_file_manager):
    with pytest.raises(SpaceFileManagerException):
        space_file_manager.list_files("missing")


def test_set_file_escape_path(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("escape")
    with pytest.raises(
        SpaceFileManagerException, match="outside space boundary"
    ):
        sfm.set_file("escape", "../../outside.txt", "nope")


def test_get_file_yaml(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("ymlspace")
    content = {"a": 1}
    sfm.set_file("ymlspace", "data.yaml", content)
    assert sfm.get_file("ymlspace", "data.yaml", load=True) == content


def test_get_file_yml(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("yml2")
    content = {"b": 2}
    sfm.set_file("yml2", "data.yml", content)
    assert sfm.get_file("yml2", "data.yml", load=True) == content


def test_get_file_json(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("jsonspace")
    content = {"key": "value"}
    sfm.set_file("jsonspace", "file.json", content)
    assert sfm.get_file("jsonspace", "file.json", load=True) == content


def test_get_file_unsupported_load(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("weird")
    sfm.set_file("weird", "raw.txt", "just text")
    result = sfm.get_file("weird", "raw.txt", load=True)
    assert isinstance(result, str)


def test_get_file_read_failure(space_file_manager, monkeypatch):
    sfm = space_file_manager
    sfm._space_manager.create_space("brokenread")
    sfm.set_file("brokenread", "fail.txt", "failme")

    broken_file_path = sfm._resolve_file_path("brokenread", "fail.txt")

    # 👇 Save original BEFORE monkeypatching
    original_read_file = FileUtils.read_file

    def selective_read(path, *args, **kwargs):
        if path == broken_file_path:
            raise FileUtilsException("Simulated read failure")
        return original_read_file(path, *args, **kwargs)  # 👈 use original

    monkeypatch.setattr(FileUtils, "read_file", selective_read)

    with pytest.raises(SpaceFileManagerException, match="Failed to read file"):
        sfm.get_file("brokenread", "fail.txt")


def test_set_file_yaml_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("y1")
    data = {"x": 123}
    assert sfm.set_file("y1", "thing.yaml", data)


def test_set_file_yml_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("y2")
    data = {"x": 456}
    assert sfm.set_file("y2", "thing.yml", data)


def test_set_file_json_success(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("j1")
    data = {"hello": "world"}
    assert sfm.set_file("j1", "thing.json", data)


def test_set_file_dict_unsupported_extension(space_file_manager):
    sfm = space_file_manager
    sfm._space_manager.create_space("dictfail")
    with pytest.raises(
        SpaceFileManagerException, match="Unsupported file extension"
    ):
        sfm.set_file("dictfail", "note.txt", {"bad": "ext"})


def test_delete_file_failure(space_file_manager, monkeypatch):
    sfm = space_file_manager
    sfm._space_manager.create_space("delerr")
    sfm.set_file("delerr", "oops.txt", "delete me")

    def explode(*args, **kwargs):
        raise OSError("delete failed")

    monkeypatch.setattr(
        "darca_file_utils.file_utils.FileUtils.remove_file", explode
    )

    with pytest.raises(Exception, match="delete failed"):
        sfm.delete_file("delerr", "oops.txt")


def test_get_file_last_modified_success(space_file_manager, space_manager):
    """
    Verify that get_file_last_modified returns a float timestamp
    and matches the filesystem mtime.
    """
    space_name = "mtime_file_success"
    space_manager.create_space(space_name)
    file_name = "example.txt"

    # Create a file in the space
    space_file_manager.set_file(space_name, file_name, "Hello, world!")

    # Retrieve actual filesystem mtime
    space_path = space_manager.get_space(space_name)["path"]
    file_path = os.path.join(space_path, file_name)
    actual_mtime = os.path.getmtime(file_path)

    # Call the method under test
    reported_mtime = space_file_manager.get_file_last_modified(
        space_name, file_name
    )

    assert isinstance(
        reported_mtime, float
    ), "Returned timestamp should be a float"
    assert (
        abs(reported_mtime - actual_mtime) < 0.0001
    ), "Reported timestamp should be within a tiny"
    " delta of the actual filesystem mtime."


def test_get_file_last_modified_nonexistent_file(
    space_file_manager, space_manager
):
    """
    If the file doesn't exist, we expect a
    SpaceFileManagerException with 'FILE_NOT_FOUND'.
    """
    space_name = "mtime_file_missing"
    space_manager.create_space(space_name)

    with pytest.raises(SpaceFileManagerException) as exc_info:
        space_file_manager.get_file_last_modified(
            space_name, "no_such_file.txt"
        )

    assert "FILE_NOT_FOUND" in str(exc_info.value)


def test_get_file_last_modified_os_error(space_file_manager, space_manager):
    """
    Force an error when retrieving os.path.getmtime,
    triggering the 'except Exception' block in get_file_last_modified.
    """
    space_name = "os_error_space"
    file_name = "failing_file.txt"

    # Create space and file so it definitely exists
    space_manager.create_space(space_name)
    space_file_manager.set_file(space_name, file_name, "Some content")

    # Mock os.path.getmtime to raise an OSError (or any other exception)
    with patch(
        "os.path.getmtime", side_effect=OSError("Mocked getmtime error")
    ):
        with pytest.raises(SpaceFileManagerException) as exc_info:
            space_file_manager.get_file_last_modified(space_name, file_name)

    # Check that the error code matches what we expect
    assert "FILE_MTIME_FAILED" in str(exc_info.value)
    assert "Error retrieving last modified time" in str(exc_info.value)
