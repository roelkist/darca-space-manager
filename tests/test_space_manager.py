# tests/test_space_manager.py

import os

import pytest

from darca_space_manager.space_manager import (
    INDEX_FILE,
    SpaceManager,
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


def test_create_space_general_failure(monkeypatch):
    from darca_space_manager.space_manager import SpaceManager

    sm = SpaceManager()
    monkeypatch.setattr(
        "darca_file_utils.directory_utils.DirectoryUtils.create_directory",
        lambda *_: (_ for _ in ()).throw(Exception("kaboom")),
    )
    with pytest.raises(SpaceManagerException, match="CREATE_SPACE_FAILED"):
        sm.create_space("crash")


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


def test_load_index_when_file_missing(monkeypatch):

    monkeypatch.setattr(
        "darca_file_utils.file_utils.FileUtils.file_exist",
        lambda path: path != INDEX_FILE,
    )

    sm = SpaceManager()
    assert isinstance(sm.index, dict)
    assert sm.index.get("spaces") == []


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
