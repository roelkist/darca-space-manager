from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Set

import pytest
import yaml

from darca_space_manager.iospace.iospace_file import (
    IOSpaceFile,
    IOSpaceFileException,
)
from darca_space_manager.metaspace.models import Space


# ───────────────────────────── dummy storage client ─────────────────────────────
class MemoryClient:
    """
    Minimal async-compatible StorageClient that keeps everything in memory.
    """

    def __init__(self):
        self.files: Dict[str, str] = {}
        self.dirs: Set[str] = {"."}

    # file ops ------------------------------------------------------------
    async def read(self, path: str, *, binary: bool = False):
        if path not in self.files:
            raise FileNotFoundError
        return self.files[path]

    async def write(
        self,
        path: str,
        content,  # str | bytes
        *,
        binary: bool = False,
        permissions=None,
        user=None,
    ):
        self.files[path] = content

    async def delete(self, path: str):
        if path in self.files:
            del self.files[path]
        else:
            raise FileNotFoundError

    async def exists(self, path: str):
        return path in self.files or path in self.dirs

    async def stat_mtime(self, path: str):
        if path not in self.files:
            raise FileNotFoundError
        return 1234.56

    async def list(self, base_path: str = ".", *, recursive: bool = False):
        if recursive:
            return list(self.files.keys())
        return [p for p in self.files if "/" not in p]

    # directory ops -------------------------------------------------------
    async def mkdir(
        self,
        path: str,
        *,
        parents: bool = True,
        permissions=None,
        user=None,
    ):
        self.dirs.add(path)

    async def rmdir(self, path: str):
        if path not in self.dirs:
            raise FileNotFoundError
        self.dirs.remove(path)

    async def rename(self, src: str, dest: str):
        if src in self.files:
            self.files[dest] = self.files.pop(src)
        elif src in self.dirs:
            self.dirs.remove(src)
            self.dirs.add(dest)
        else:
            raise FileNotFoundError


# ───────────────────────────── helpers / fixtures ─────────────────────────────
@pytest.fixture
def iospace(monkeypatch) -> IOSpaceFile:
    """
    A fresh IOSpaceFile bound to an in-memory client, with YAML helpers patched
    to in-memory maps as well.
    """
    client = MemoryClient()
    space = Space(
        name="demo",
        repository="repo1",
        created_at=datetime.now(timezone.utc),
        last_modified_at=datetime.now(timezone.utc),
    )

    # Patch YamlUtils to keep YAML docs in memory so no real FS is touched
    yaml_store: Dict[str, str] = {}

    def fake_save_yaml(path, data):
        yaml_store[path] = yaml.safe_dump(data)

    def fake_load_yaml(path):
        return yaml.safe_load(yaml_store[path])

    monkeypatch.setattr(
        "darca_space_manager.iospace.iospace_file.YamlUtils.save_yaml_file",
        fake_save_yaml,
    )
    monkeypatch.setattr(
        "darca_space_manager.iospace.iospace_file.YamlUtils.load_yaml_file",
        fake_load_yaml,
    )

    return IOSpaceFile(space=space, client=client)


# ───────────────────────────── success paths ─────────────────────────────
@pytest.mark.asyncio
async def test_write_read_string(iospace: IOSpaceFile):
    await iospace.write_file("hello.txt", "hi")
    assert await iospace.read_file("hello.txt") == "hi"


@pytest.mark.asyncio
async def test_yaml_roundtrip(iospace: IOSpaceFile):
    data = {"a": 1}
    await iospace.write_file("cfg.yaml", data)
    assert await iospace.read_file("cfg.yaml", load=True) == data


@pytest.mark.asyncio
async def test_json_roundtrip(iospace: IOSpaceFile):
    data = {"b": 2}
    await iospace.write_file("doc.json", data)
    assert await iospace.read_file("doc.json", load=True) == data


@pytest.mark.asyncio
async def test_dir_ops_and_listing(iospace: IOSpaceFile):
    await iospace.create_dir("data")
    await iospace.write_file("data/x.txt", "x")
    files = await iospace.list_files(recursive=True)
    assert "data/x.txt" in files

    await iospace.move("data/x.txt", "data/y.txt")
    assert await iospace.file_exists("data/y.txt")

    mtime = await iospace.file_last_modified("data/y.txt")
    assert mtime == 1234.56

    await iospace.delete_file("data/y.txt")
    await iospace.delete_dir("data")
    assert not await iospace.file_exists("data/y.txt")


# ───────────────────────────── error paths ─────────────────────────────
@pytest.mark.asyncio
async def test_write_dict_unsupported_ext_raises(iospace: IOSpaceFile):
    with pytest.raises(IOSpaceFileException):
        await iospace.write_file("bad.txt", {"oops": True})


@pytest.mark.asyncio
async def test_read_missing_raises(iospace: IOSpaceFile):
    with pytest.raises(IOSpaceFileException):
        await iospace.read_file("missing.txt")


@pytest.mark.asyncio
async def test_delete_missing_raises(iospace: IOSpaceFile):
    with pytest.raises(IOSpaceFileException):
        await iospace.delete_file("ghost.txt")


@pytest.mark.asyncio
async def test_create_dir_failure_is_wrapped(iospace: IOSpaceFile, monkeypatch):
    # make the underlying client raise an exception
    async def broken_mkdir(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(iospace._client, "mkdir", broken_mkdir)

    with pytest.raises(IOSpaceFileException):
        await iospace.create_dir("fail")


@pytest.mark.asyncio
async def test_exists_error_path(iospace: IOSpaceFile, monkeypatch):
    async def broken_exists(*_a, **_kw):
        raise RuntimeError

    monkeypatch.setattr(iospace._client, "exists", broken_exists)

    with pytest.raises(IOSpaceFileException):
        await iospace.file_exists("whatever")
