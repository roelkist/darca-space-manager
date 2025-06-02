# tests/conftest.py
# License: MIT

import os
from pathlib import Path
import shutil
import tempfile
import pytest
import yaml

from darca_space_manager.config import ensure_directories_exist
from darca_space_manager.lock.file_lock_manager import FileLockManager
from darca_space_manager.api.space_service import SpaceService
from darca_space_manager.metaspace.yaml_metaspace_backend import YamlMetaspaceBackend
from darca_space_manager.masterspace.masterspace_backend import MasterspaceBackend
from darca_space_manager.masterspace.masterspace_repository_backend import (
    RepositoryMasterspaceBackend,
)
from darca_space_manager import config

from darca_repository.models import Repository, StorageScheme
from darca_storage.backends.local_file_backend import LocalFileBackend  
from darca_storage.decorators.scoped_backend import ScopedFileBackend
from darca_storage.client import StorageClient


@pytest.fixture(scope="session")
def test_env_dir():
    """Isolated test environment for DARCA_SPACE_BASE"""
    base_dir = tempfile.mkdtemp(prefix="darca-test-env-")
    os.environ["DARCA_SPACE_BASE"] = base_dir
    config.ensure_directories_exist()
    yield base_dir
    shutil.rmtree(base_dir, ignore_errors=True)
    os.environ.pop("DARCA_SPACE_BASE", None)


@pytest.fixture
def test_repository(test_env_dir):
    """Fake file:// repository using the test space dir"""
    space_dir = config.get_directories()["SPACE_DIR"]
    return Repository(
        name="test-repo",
        storage_url=f"file://{space_dir}",
        scheme=StorageScheme.FILE,
        credentials=None,
        parameters={},
        tags={"test": "true"},
    )


@pytest.fixture
def mock_storage_client(test_repository):
    path = test_repository.storage_url[len("file://"):]
    backend = ScopedFileBackend(LocalFileBackend(), base_path=path)
    return StorageClient(backend=backend)


class StaticMasterspaceBackend(MasterspaceBackend):
    def __init__(self, client: StorageClient, repository_name: str):
        self._client = client
        self._repo_name = repository_name

    async def get_client(self, space_name: str) -> StorageClient:
        # You can optionally assert against space_name or skip for test generality
        return self._client


@pytest.fixture
def masterspace_backend(test_repository, mock_storage_client):
    return StaticMasterspaceBackend(mock_storage_client, test_repository.name)


@pytest.fixture
def metaspace():
    return YamlMetaspaceBackend()


@pytest.fixture
def lock_manager():
    return FileLockManager()


@pytest.fixture
def space_service(metaspace, lock_manager, masterspace_backend):
    return SpaceService(
        metaspace=metaspace,
        lock_manager=lock_manager,
        masterspace_backend=masterspace_backend,
    )

@pytest.fixture
def space_service_smoke(tmp_path: Path) -> SpaceService:
    """
    Returns a *live* SpaceService wired to an isolated repository
    hierarchy under pytest’s tmpdir.
    """
    # Directory layout ───────────────────────────────────────────────
    base          = tmp_path / "darca"
    cfg_dir       = base / "repo" / "config"
    stores_dir    = base / "repo" / "stores" / "repo1"
    manager_dir   = base / "repo" / "manager"

    cfg_dir.mkdir(parents=True, exist_ok=True)
    stores_dir.mkdir(parents=True, exist_ok=True)
    manager_dir.mkdir(parents=True, exist_ok=True)

    # Repository profile (YAML) ──────────────────────────────────────
    profile = {
        "name": "repo1",
        "storage_url": f"file://{stores_dir}",
        "scheme": "file",
    }
    (cfg_dir / "repo1.yaml").write_text(yaml.safe_dump(profile))

    # Environment so that darca_* modules discover the temp tree
    os.environ.update(
        DARCA_REPOSITORY_MODE="yaml",
        DARCA_REPOSITORY_PROFILE_DIR=str(cfg_dir),
        DARCA_SPACE_BASE=str(manager_dir),
    )

    # Ensure <manager>/metadata etc. exist
    ensure_directories_exist()

    # Fully-wired service instance
    return SpaceService(
        metaspace=YamlMetaspaceBackend(),
        lock_manager=FileLockManager(),
        masterspace_backend=RepositoryMasterspaceBackend(),
    )