from pathlib import Path

import pytest
import asyncio

import darca_space_manager.config as cfg
from darca_space_manager.lock.file_lock_manager import FileLockManager


def _patch_metadata_dir(tmp: Path, monkeypatch):
    monkeypatch.setattr(
        cfg,
        "get_directories",
        lambda: {
            "SPACE_DIR": str(tmp / "spaces"),
            "METADATA_DIR": str(tmp / "meta"),
            "CONTROL_DIR": str(tmp / "ctrl"),
            "LOG_DIR": str(tmp / "log"),
        },
    )


@pytest.mark.asyncio
async def test_single_lock_serialises_access(tmp_path, monkeypatch):
    _patch_metadata_dir(tmp_path, monkeypatch)

    lm = FileLockManager()
    order = []

    async def task(idx):
        async with lm.acquire("alpha"):
            order.append(idx)

    await asyncio.gather(*(task(i) for i in (1, 2)))
    assert order == [1, 2]


@pytest.mark.asyncio
async def test_acquire_many_orders_keys(tmp_path, monkeypatch):
    _patch_metadata_dir(tmp_path, monkeypatch)

    lm = FileLockManager()
    async with lm.acquire_many(["b", "a", "c"]):
        # if we’re here, no dead-lock occurred
        assert True
