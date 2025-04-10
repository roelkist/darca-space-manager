# tests/conftest.py

import shutil
import tempfile

import pytest

from darca_space_manager.space_file_manager import SpaceFileManager
from darca_space_manager.space_manager import SpaceManager


@pytest.fixture(scope="function")
def temp_darca_env(monkeypatch):
    """
    Fixture to isolate each test with a unique DARCA_SPACE_BASE.
    Supports parallel execution (xdist) by using a unique temp dir.
    """
    temp_dir = tempfile.mkdtemp(prefix="darca_test_env_")
    monkeypatch.setenv("DARCA_SPACE_BASE", temp_dir)

    # Force config to re-evaluate with new env var
    # We reload config module to re-trigger path creation
    import importlib

    import darca_space_manager.config as darca_config

    importlib.reload(darca_config)

    yield temp_dir

    # Cleanup after test
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
