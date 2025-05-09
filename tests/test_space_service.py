import pytest
import uuid
from darca_space_manager import SpaceService, SpaceURI


def unique_space_name(prefix="space") -> str:
    """Generates a unique space name to avoid collisions in parallel test runs."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_and_get_space(isolated_service: SpaceService):
    name = unique_space_name("create")
    space = isolated_service.create_space(name, label="x")
    assert space.name == name
    assert space.label == "x"
    assert isolated_service.get_space(name).name == name


def test_write_read_file(isolated_service: SpaceService):
    name = unique_space_name("alpha")
    isolated_service.create_space(name)

    uri = SpaceURI.from_str(f"space://{name}/test.yaml")
    content = {"env": "test", "version": 1}

    isolated_service.write_file(uri, content)
    result = isolated_service.read_file(uri, load=True)

    assert result["env"] == "test"
    assert result["version"] == 1


def test_rename_space(isolated_service: SpaceService):
    old = unique_space_name("old")
    new = unique_space_name("new")

    isolated_service.create_space(old)
    renamed = isolated_service.rename_space(old, new)

    assert renamed.name == new
    assert "new" in renamed.name
    assert isolated_service.get_space(old) is None
    assert isolated_service.get_space(new).name == new


def test_delete_space(isolated_service: SpaceService):
    name = unique_space_name("del")
    isolated_service.create_space(name)
    isolated_service.delete_space(name)

    assert isolated_service.get_space(name) is None


def test_force_delete_nested(isolated_service: SpaceService):
    root = unique_space_name("root")
    child = unique_space_name("child")

    isolated_service.create_space(root)
    isolated_service.create_space(child, parent=root)

    with pytest.raises(Exception):
        isolated_service.delete_space(root)

    isolated_service._manager.delete_space(root, force=True)

    assert isolated_service.get_space(root) is None
    assert isolated_service.get_space(child) is None


def test_run_command(isolated_service: SpaceService):
    name = unique_space_name("exec")
    isolated_service.create_space(name)

    uri = f"space://{name}/"
    result = isolated_service.run(uri, ["echo", "it_works"], capture_output=True)

    assert result.returncode == 0
    assert "it_works" in result.stdout.strip()

def test_file_exists_and_delete(isolated_service: SpaceService):
    name = unique_space_name("delta")
    isolated_service.create_space(name)

    uri = SpaceURI.from_str(f"space://{name}/check.txt")
    isolated_service.write_file(uri, "hello")

    assert isolated_service.file_exists(uri)
    assert isolated_service.delete_file(uri)
    assert not isolated_service.file_exists(uri)

def test_list_files(isolated_service: SpaceService):
    name = unique_space_name("ls")
    isolated_service.create_space(name)

    isolated_service.write_file(SpaceURI.from_str(f"space://{name}/a.txt"), "1")
    isolated_service.write_file(SpaceURI.from_str(f"space://{name}/b.txt"), "2")

    files = isolated_service.list_files(name)
    assert any("a.txt" in f for f in files)
    assert any("b.txt" in f for f in files)

def test_list_files_content_ascii(isolated_service: SpaceService):
    name = unique_space_name("ascii")
    isolated_service.create_space(name)

    uri = SpaceURI.from_str(f"space://{name}/info.txt")
    isolated_service.write_file(uri, "ASCII content")

    contents = isolated_service.list_files_content(name)
    assert any(file["type"] == "ascii" for file in contents)
    assert any("ASCII content" in file["file_content"] for file in contents)

def test_get_file_last_modified(isolated_service: SpaceService):
    import time

    name = unique_space_name("mtime")
    isolated_service.create_space(name)

    uri = SpaceURI.from_str(f"space://{name}/data.json")
    isolated_service.write_file(uri, {"key": "val"})

    modified = isolated_service.file_last_modified(uri)
    assert modified > 0

