import pytest

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
