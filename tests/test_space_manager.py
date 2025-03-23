import os

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
    # Create the space first so the directory exists
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
    assert space_manager.space_exists(unique_space_name)
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
    """Force DirectoryUtils.list_directory to fail"""
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.list_directory",
        lambda *_: (_ for _ in ()).throw(Exception("fail")),
    )
    with pytest.raises(SpaceManagerException):
        space_manager.list_spaces()


def test_create_space_exception(monkeypatch, space_manager, unique_space_name):
    """Simulate DirectoryUtils.create_directory failure"""
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.create_directory",
        lambda *_: False,
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.directory_exist",
        lambda *_: False,
    )
    # Force the metadata write to succeed so it reaches the directory logic
    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file",
        lambda *_args, **_kwargs: True,
    )
    with pytest.raises(SpaceManagerException, match="Failed to create space directory"):
        space_manager.create_space(unique_space_name)


def test_save_metadata_exception(monkeypatch, space_manager, unique_space_name):
    """Simulate YamlUtils.save_yaml_file failure"""
    monkeypatch.setattr(
        "darca_space_manager.space_manager.YamlUtils.save_yaml_file",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(Exception("boom")),
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.directory_exist",
        lambda *_: True,
    )
    with pytest.raises(SpaceManagerException, match="Failed to save metadata"):
        space_manager.create_space(unique_space_name, metadata={"fail": True})


def test_get_metadata_path_fail(monkeypatch, space_manager):
    """Simulate failure to build metadata path by mocking metadata_dir to an invalid object."""
    class BadPath:
        def __str__(self): raise Exception("metadata_dir is broken")

    monkeypatch.setattr(space_manager, "metadata_dir", BadPath())
    with pytest.raises(SpaceManagerException, match="Failed to determine metadata path"):
        space_manager.get_space_metadata("whatever")


def test_read_metadata_exception(monkeypatch, space_manager, unique_space_name):
    """Simulate FileUtils.read_file failure"""
    monkeypatch.setattr(
        "darca_space_manager.space_manager.FileUtils.read_file",
        lambda *_: (_ for _ in ()).throw(Exception("read boom")),
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.directory_exist",
        lambda *_: True,
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.create_directory",
        lambda *_: True,
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.FileUtils.write_file",
        lambda *_: True,
    )
    space_manager.create_space(unique_space_name, metadata={"x": 1})
    with pytest.raises(SpaceManagerException, match="Failed to read metadata"):
        space_manager.get_space_metadata(unique_space_name)


def test_write_metadata_exception(monkeypatch, space_manager, unique_space_name):
    """Simulate FileUtils.write_file failure during metadata write"""
    monkeypatch.setattr(
        "darca_space_manager.space_manager.FileUtils.write_file",
        lambda *_: (_ for _ in ()).throw(Exception("write boom")),
    )
    monkeypatch.setattr(
        "darca_space_manager.space_manager.DirectoryUtils.directory_exist",
        lambda *_: True,
    )
    with pytest.raises(SpaceManagerException, match="Failed to write metadata"):
        space_manager.create_space(unique_space_name, metadata={"bad": True})