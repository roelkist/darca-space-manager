# tests/conftest.py

import shutil
import tempfile

import pytest

from darca_space_manager.space_file_manager import SpaceFileManager
from darca_space_manager.space_manager import SpaceManager


@pytest.fixture(scope="function")
def temp_darca_env(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="darca_test_env_")
    monkeypatch.setenv("DARCA_SPACE_BASE", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def space_manager(temp_darca_env):
    """
    Provides a fresh SpaceManager instance using the isolated temp config.
    """
    return SpaceManager()


@pytest.fixture(scope="function")
def space_file_manager(temp_darca_env):
    """
    Provides a fresh SpaceFileManager instance using the isolated temp config.
    """
    return SpaceFileManager()
