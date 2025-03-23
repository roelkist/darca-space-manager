import pytest
from darca_file_utils.file_utils import FileUtils

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


def test_get_metadata_success(
    space_manager, unique_space_name, sample_metadata
):
    assert space_manager.create_space(
        unique_space_name, metadata=sample_metadata
    )
    metadata = space_manager.get_space_metadata(unique_space_name)
    assert metadata["owner"] == sample_metadata["owner"]


def test_get_metadata_failure(space_manager):
    with pytest.raises(SpaceManagerException):
        space_manager.get_space_metadata("non_existent_space")


def test_delete_space(space_manager, unique_space_name, sample_metadata):
    assert space_manager.create_space(
        unique_space_name, metadata=sample_metadata
    )
    assert space_manager.delete_space(unique_space_name)
    assert not space_manager.space_exists(unique_space_name)


def test_delete_nonexistent(space_manager):
    with pytest.raises(SpaceManagerException):
        space_manager.delete_space("ghost_space")


def test_metadata_only_delete(
    space_manager, unique_space_name, sample_metadata
):
    space_manager.create_space(unique_space_name, metadata=sample_metadata)
    metadata_path = space_manager._get_metadata_path(unique_space_name)
    assert FileUtils.remove_file(metadata_path)
    assert space_manager.delete_space(unique_space_name)


def test_list_spaces_exception(monkeypatch, space_manager):
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.list_directory",
        lambda *_: (_ for _ in ()).throw(Exception("fail")),
    )
    with pytest.raises(SpaceManagerException):
        space_manager.list_spaces()


def test_create_space_metadata_none(monkeypatch, tmp_path):
    """Cover case where metadata=None"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )
    space_manager = SpaceManager()
    assert space_manager.create_space("minimal_space", metadata=None)


def test_create_space_metadata_empty(monkeypatch, tmp_path):
    """Cover lines 118-119 when metadata is empty dict"""
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )
    space_manager = SpaceManager()
    assert space_manager.create_space("empty_meta", metadata={})


def test_create_space_exception(monkeypatch, tmp_path):
    """Simulate YamlUtils.save_yaml_file failure (rollback succeeds)"""
    base_dir = tmp_path / "darca_space"
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(base_dir / "spaces"),
            "METADATA_DIR": str(base_dir / "metadata"),
            "LOG_DIR": str(base_dir / "logs"),
        },
    )
    space_manager = SpaceManager()
    name = "failing_space"

    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.create_directory",
        lambda *_: True,
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file",
        lambda *_: (_ for _ in ()).throw(Exception("force metadata fail")),
    )

    # ✅ Let rollback succeed this time
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.remove_directory",
        lambda *_: True,
    )

    with pytest.raises(
        SpaceManagerException, match="Failed to store metadata"
    ):
        space_manager.create_space(name, metadata={"some": "data"})


def test_save_metadata_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )
    space_manager = SpaceManager()

    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(Exception("boom")),
    )

    with pytest.raises(
        SpaceManagerException, match="Failed to store metadata"
    ):
        space_manager.create_space("new_space", metadata={"fail": True})


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


def test_write_metadata_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(tmp_path / "spaces"),
            "METADATA_DIR": str(tmp_path / "metadata"),
            "LOG_DIR": str(tmp_path / "logs"),
        },
    )
    space_manager = SpaceManager()

    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file",
        lambda *_: (_ for _ in ()).throw(Exception("write boom")),
    )

    with pytest.raises(
        SpaceManagerException, match="Failed to store metadata"
    ):
        space_manager.create_space("newspace", metadata={"bad": True})


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
