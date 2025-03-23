from unittest.mock import patch
from uuid import uuid4

import pytest
from darca_file_utils.directory_utils import DirectoryUtils

from darca_space_manager.space_manager import (
    SpaceManager,
    SpaceManagerException,
)


def test_create_and_exist(space_manager, unique_space_name):
    assert not space_manager.space_exists(unique_space_name)
    assert space_manager.create_space(unique_space_name)
    assert space_manager.space_exists(unique_space_name)


def test_duplicate_create(space_manager, unique_space_name):
    assert space_manager.create_space(unique_space_name)
    with pytest.raises(SpaceManagerException):
        space_manager.create_space(unique_space_name)


def test_list_and_count(space_manager, unique_space_name):
    assert space_manager.create_space(unique_space_name)
    before = set(space_manager.list_spaces())
    assert unique_space_name in before
    assert space_manager.count_spaces() == len(before)


def test_delete_space(space_manager, unique_space_name, sample_metadata):
    assert space_manager.create_space(unique_space_name)
    assert space_manager.delete_space(unique_space_name)
    assert not space_manager.space_exists(unique_space_name)


def test_delete_nonexistent(space_manager):
    with pytest.raises(SpaceManagerException):
        space_manager.delete_space("ghost_space")


def test_list_spaces_exception(monkeypatch, space_manager):
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.list_directory",
        lambda *_: (_ for _ in ()).throw(Exception("fail")),
    )
    with pytest.raises(SpaceManagerException):
        space_manager.list_spaces()


def test_get_metadata_path_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )

    (tmp_path / "spaces" / "broken_space").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        "darca_space_manager.space_manager.SpaceManager._get_metadata_path",
        lambda *_: (_ for _ in ()).throw(Exception("bad join")),
    )

    space_manager = SpaceManager()

    with pytest.raises(SpaceManagerException, match="Failed to load metadata"):
        space_manager.get_space_metadata("broken_space")


def test_read_metadata_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )
    space_manager = SpaceManager()
    name = "testspace"
    (tmp_path / "spaces" / name).mkdir(parents=True)

    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.load_yaml_file",
        lambda *_: (_ for _ in ()).throw(Exception("read boom")),
    )

    with pytest.raises(SpaceManagerException, match="Failed to load metadata"):
        space_manager.get_space_metadata(name)


def test_delete_metadata_file_missing(monkeypatch, tmp_path):
    """Covers lines 201–202 (FileUtils.file_exist returns False)"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )

    name = "nometafile"
    (tmp_path / "spaces" / name).mkdir(parents=True)

    space_manager = SpaceManager()
    assert space_manager.delete_space(name)


def test_delete_metadata_failure(monkeypatch, tmp_path):
    """Covers lines 213–214 (FileUtils.remove_file fails)"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )

    name = "failmeta"
    space_path = tmp_path / "spaces" / name
    space_path.mkdir(parents=True)

    meta_path = tmp_path / "metadata" / f"{name}.yaml"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text("owner: foo")

    monkeypatch.setattr(
        "darca_space_manager.space_manager.FileUtils.remove_file",
        lambda *_: (_ for _ in ()).throw(Exception("delete fail")),
    )

    space_manager = SpaceManager()

    with pytest.raises(
        SpaceManagerException, match="Failed to delete metadata"
    ):
        space_manager.delete_space(name)


def test_create_directory_failure(monkeypatch, tmp_path):
    """Simulate failure in DirectoryUtils.create_directory"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )

    space_manager = SpaceManager()

    # Simulate directory creation failure
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.create_directory",
        lambda *_: (_ for _ in ()).throw(Exception("mkdir fail")),
    )

    with pytest.raises(SpaceManagerException, match="Failed to create space"):
        space_manager.create_space("mkdir_fail_space")


def test_delete_directory_failure(monkeypatch, tmp_path):
    """Simulate failure in DirectoryUtils.remove_directory"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )

    space_manager = SpaceManager()
    name = "undeletable_space"

    # Set up existing space directory
    (tmp_path / "spaces" / name).mkdir(parents=True)

    # Simulate directory deletion failure
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.remove_directory",
        lambda *_: (_ for _ in ()).throw(Exception("rmdir fail")),
    )

    with pytest.raises(
        SpaceManagerException, match="Failed to delete space directory"
    ):
        space_manager.delete_space(name)


def unique_space_name() -> str:
    return "testspace_" + uuid4().hex


def test_create_space_metadata_failure_triggers_rollback():
    manager = SpaceManager()
    space = unique_space_name()

    with patch(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file"
    ) as mock_save:
        mock_save.side_effect = RuntimeError("Simulated failure")

        with pytest.raises(SpaceManagerException) as exc:
            manager.create_space(space)

        assert exc.value.error_code == "METADATA_WRITE_FAILED"
        # Line 154: Metadata save failed
        # Line 156: DirectoryUtils.remove_directory called
        # Line 157: Exception raised for failure
        assert not DirectoryUtils.directory_exist(
            manager._get_space_path(space)
        )


def test_get_space_metadata_nonexistent_space_triggers_exception():
    manager = SpaceManager()
    space = "nonexistent_" + uuid4().hex

    with pytest.raises(SpaceManagerException) as exc:
        manager.get_space_metadata(space)

    assert exc.value.error_code == "SPACE_NOT_FOUND"
