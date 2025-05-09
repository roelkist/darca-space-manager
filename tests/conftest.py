import os
import shutil
import tempfile
import logging

import pytest


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Minimal logging config for test sessions."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )


@pytest.fixture
def darca_base_env(monkeypatch):
    """
    Patch DARCA_SPACE_BASE to a temporary directory.
    Automatically used in other fixtures that depend on it.
    """
    tmp_dir = tempfile.mkdtemp(prefix="darca_test_")
    monkeypatch.setenv("DARCA_SPACE_BASE", tmp_dir)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def isolated_service(darca_base_env):
    """
    Returns a fresh instance of SpaceService in a clean DARCA env.
    """
    from darca_space_manager import SpaceService
    return SpaceService()
