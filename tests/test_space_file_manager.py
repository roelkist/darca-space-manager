import os
from uuid import uuid4

import pytest

from darca_space_manager.space_file_manager import (
    SpaceFileManager,
    SpaceFileManagerException,
)


def unique_filename(ext: str) -> str:
    return f"file_{uuid4().hex}{ext}"


def test_set_and_get_text_file(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    content = "Hello, ASCII!"
    assert manager.set_file(space, filename, content)
    assert manager.get_file(space, filename) == content


def test_set_and_get_yaml(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".yaml")
    data = {"project": "darca", "version": 1}
    assert manager.set_file(space, filename, data)
    result = manager.get_file(space, filename)
    assert "project: darca" in result


def test_set_and_get_yml(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".yml")
    data = {"foo": "bar"}
    assert manager.set_file(space, filename, data)
    result = manager.get_file(space, filename)
    assert "foo: bar" in result


def test_set_and_get_json(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".json")
    data = {"key": "value", "numbers": [1, 2]}
    assert manager.set_file(space, filename, data)
    result = manager.get_file(space, filename)
    assert '"key": "value"' in result


def test_file_exists(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    manager.set_file(space, filename, "exists")
    assert manager.file_exists(space, filename)


def test_delete_file(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    manager.set_file(space, filename, "remove me")
    assert manager.delete_file(space, filename)
    assert not manager.file_exists(space, filename)


def test_list_files(space_file_manager):
    manager, space = space_file_manager
    files = [
        unique_filename(".a"),
        unique_filename(".b"),
        unique_filename(".c"),
    ]
    for f in files:
        manager.set_file(space, f, "test content")
    listed = manager.list_files(space)
    assert all(f in listed for f in files)


def test_get_file_outside_space_raises(space_file_manager):
    manager, space = space_file_manager
    with pytest.raises(
        SpaceFileManagerException, match="outside of space boundary"
    ):
        manager.get_file(space, "../hax.txt")


def test_set_file_with_unsupported_dict_extension(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    with pytest.raises(
        SpaceFileManagerException, match="Unsupported file extension"
    ):
        manager.set_file(space, filename, {"key": "val"})


def test_set_file_with_invalid_type(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    with pytest.raises(
        SpaceFileManagerException, match="Unsupported content type"
    ):
        manager.set_file(space, filename, 12345)


def test_get_file_non_ascii(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".txt")
    file_path = os.path.join(
        manager._space_manager._get_space_path(space), filename
    )
    with open(file_path, "wb") as f:
        f.write("Café au lait".encode("utf-8"))
    with pytest.raises(SpaceFileManagerException, match="FILE_READ_FAILED"):
        manager.get_file(space, filename)


def test_delete_non_existent_file(space_file_manager):
    manager, space = space_file_manager
    filename = unique_filename(".ghost")
    with pytest.raises(SpaceFileManagerException, match="FILE_DELETE_FAILED"):
        manager.delete_file(space, filename)


def test_list_files_in_missing_space():
    sfm = SpaceFileManager()
    missing_space = "missing_" + uuid4().hex
    with pytest.raises(SpaceFileManagerException, match="LIST_FILES_FAILED"):
        sfm.list_files(missing_space)


def test_set_file_json_dumps_failure_triggers_generic_exception(
    space_file_manager,
):
    manager, space = space_file_manager
    filename = unique_filename(".json")

    content = {"key": lambda x: x}  # Not JSON serializable

    with pytest.raises(SpaceFileManagerException) as exc:
        manager.set_file(space, filename, content)

    assert exc.value.error_code == "FILE_WRITE_FAILED"
    assert "Failed to write file" in str(exc.value)


def test_resolve_file_path_raises_on_nonexistent_space():
    manager = SpaceFileManager()
    nonexistent_space = "does_not_exist_" + uuid4().hex

    with pytest.raises(SpaceFileManagerException) as exc:
        manager.get_file(nonexistent_space, "file.txt")

    assert exc.value.error_code == "SPACE_NOT_FOUND"
