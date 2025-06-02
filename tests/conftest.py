# tests/conftest.py
# License: MIT

import os
import shutil
import tempfile
import pytest

from darca_space_manager.lock.file_lock_manager import FileLockManager
from darca_space_manager.api.space_service import SpaceService
from darca_space_manager.metaspace.yaml_metaspace_backend import YamlMetaspaceBackend
from darca_space_manager.masterspace.masterspace_backend import MasterspaceBackend
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
