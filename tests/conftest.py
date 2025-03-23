import os
import uuid

import pytest

from darca_space_manager.space_file_manager import SpaceFileManager
from darca_space_manager.space_manager import SpaceManager


@pytest.fixture
def temp_config(monkeypatch, tmp_path):
    base = tmp_path / "darca_space"
    monkeypatch.setattr(
        "darca_space_manager.config.DIRECTORIES",
        {
            "SPACE_DIR": str(base / "spaces"),
            "METADATA_DIR": str(base / "metadata"),
            "LOG_DIR": str(base / "logs"),
        },
    )
    yield


@pytest.fixture
def space_manager(temp_config):
    return SpaceManager()


@pytest.fixture
def sample_metadata():
    return {"owner": "tester", "purpose": "unit test", "version": 1}


@pytest.fixture
def unique_space_name(tmp_path_factory):
    # Unique per test
    return f"space_{tmp_path_factory.mktemp('spacetest').name}"


@pytest.fixture(scope="function")
def space_file_manager(space_manager):
    """
    Provides a SpaceFileManager instance and a uniquely-named test space.
    Ensures isolation for parallel test execution.
    """
    unique_space = f"testspace_{uuid.uuid4().hex}"
    os.makedirs(space_manager._get_space_path(unique_space), exist_ok=True)
    return SpaceFileManager(space_manager=space_manager), unique_space
