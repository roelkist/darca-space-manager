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


def test_list_files_content_success(space_file_manager, space_manager):
    """
    Create a space with:
      - An ASCII file
      - A binary file
      - A subdirectory with a file
    Then confirm list_files_content returns correct entries.
    """
    space_name = "files_content_space"
    space_manager.create_space(space_name)
    space_path = space_manager.get_space(space_name)["path"]

    # 1) ASCII file
    ascii_file_rel = "hello.txt"
    ascii_file_path = os.path.join(space_path, ascii_file_rel)
    with open(ascii_file_path, "w", encoding="ascii") as f:
        f.write("This is ASCII content")

    # 2) Binary file
    bin_file_rel = "image.bin"
    bin_file_path = os.path.join(space_path, bin_file_rel)
    with open(bin_file_path, "wb") as f:
        f.write(b"\x00\xff\x00\xff")

    # 3) Subdirectory with a file (also ASCII for demonstration)
    sub_dir = os.path.join(space_path, "subdir")
    os.makedirs(sub_dir, exist_ok=True)
    sub_file_rel = "subdir/nested.txt"
    sub_file_path = os.path.join(space_path, sub_file_rel)
    with open(sub_file_path, "w", encoding="ascii") as f:
        f.write("Inside subdirectory")

    # Now call the method
    results = space_file_manager.list_files_content(space_name)
    # We expect 3 entries total (the directory "subdir" is skipped
    # since it's not a file)
    assert len(results) == 4  # FIXME Metadata.yaml part of list

    # Sort results by file_name so we can check them easily
    results_sorted = sorted(results, key=lambda x: x["file_name"])

    # 1) ASCII file
    assert results_sorted[0]["file_name"] == ascii_file_rel
    assert results_sorted[0]["type"] == "ascii"
    assert results_sorted[0]["file_content"] == "This is ASCII content"

    # 2) Binary file
    assert results_sorted[1]["file_name"] == bin_file_rel
    assert results_sorted[1]["type"] == "binary"
    assert results_sorted[1]["file_content"] is None

    # 3) Subdirectory file
    assert results_sorted[3]["file_name"] == sub_file_rel
    assert results_sorted[3]["type"] == "ascii"
    assert results_sorted[3]["file_content"] == "Inside subdirectory"


def test_list_files_content_space_not_found(space_file_manager):
    """
    If the space doesn't exist, list_files_content should raise
    SpaceFileManagerException.
    """
    with pytest.raises(SpaceFileManagerException) as exc_info:
        space_file_manager.list_files_content("no_such_space")
    assert "SPACE_NOT_FOUND" in str(exc_info.value)


def test_list_files_content_file_read_error(space_file_manager, space_manager):
    """
    If reading a file fails (IOError), we log a warning and skip that file.
    We'll use mock_open with side_effect to simulate an I/O error.
    """
    space_name = "file_read_error_space"
    space_manager.create_space(space_name)
    space_path = space_manager.get_space(space_name)["path"]

    # Create a file that we'll fail to read
    fail_file_rel = "failme.txt"
    fail_file_path = os.path.join(space_path, fail_file_rel)
    with open(fail_file_path, "w") as f:
        f.write("unreachable content")

    # Create a normal ASCII file to confirm that it is read successfully
    ascii_file_rel = "good.txt"
    ascii_file_path = os.path.join(space_path, ascii_file_rel)
    with open(ascii_file_path, "w") as f:
        f.write("Hello world")

    # We'll patch builtins.open to raise an exception only for fail_file
    original_open = open

    def mocked_open(path, mode="r", *args, **kwargs):
        if fail_file_rel in path:
            raise IOError("Mocked I/O error")
        return original_open(path, mode, *args, **kwargs)

    with patch("builtins.open", side_effect=mocked_open):
        results = space_file_manager.list_files_content(space_name)

    # Sort results by file_name so we can check them easily
    results_sorted = sorted(results, key=lambda x: x["file_name"])

    # We expect only 1 result: the "good.txt"
    assert len(results) == 2  # FIXME Metadata.yaml part of list
    assert results_sorted[0]["file_name"] == ascii_file_rel
    assert results_sorted[0]["type"] == "ascii"
    assert results_sorted[0]["file_content"] == "Hello world"


def test_list_files_content_listing_error(space_file_manager):
    """
    If list_files fails unexpectedly, we catch it and raise
    SpaceFileManagerException
    with code LIST_FILES_CONTENT_FAILED.
    """
    space_name = "listing_error_space"

    # Mock list_files to throw an exception
    with patch.object(
        space_file_manager,
        "list_files",
        side_effect=RuntimeError("Mocked error"),
    ):
        with pytest.raises(SpaceFileManagerException) as exc_info:
            space_file_manager.list_files_content(space_name)

    assert "LIST_FILES_CONTENT_FAILED" in str(exc_info.value)
    assert "listing_error_space" in str(exc_info.value)
