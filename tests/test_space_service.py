# tests/test_space_service.py
# License: MIT

import pytest
from pathlib import Path
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_create_and_read_file(space_service, test_repository):
    await space_service.create_space(
        name="demo",
        repository=test_repository.name,
        label="test"
    )

    uri = "space://demo/hello.txt"
    await space_service.write_file(uri, "Hello from Darca")

    assert await space_service.file_exists(uri)

    content = await space_service.read_file(uri)
    assert content == "Hello from Darca"

    await space_service.delete_file(uri)
    assert not await space_service.file_exists(uri)


@pytest.mark.asyncio
async def test_create_and_remove_directory(space_service, test_repository):
    await space_service.create_space(
        name="data",
        repository=test_repository.name
    )

    dir_uri = "space://data/subfolder"
    file_uri = "space://data/subfolder/info.txt"

    await space_service.create_dir(dir_uri)
    await space_service.write_file(file_uri, "metadata")

    assert await space_service.read_file(file_uri) == "metadata"

    await space_service.delete_dir(dir_uri)
    assert not await space_service.file_exists(file_uri)


@pytest.mark.asyncio
async def test_move_file(space_service, test_repository):
    await space_service.create_space(
        name="mvtest",
        repository=test_repository.name
    )

    old_uri = "space://mvtest/old.txt"
    new_uri = "space://mvtest/new.txt"

    await space_service.write_file(old_uri, "version1")
    await space_service.move_path(old_uri, new_uri)

    assert await space_service.file_exists(new_uri)
    assert not await space_service.file_exists(old_uri)

    content = await space_service.read_file(new_uri)
    assert content == "version1"

@pytest.mark.asyncio
async def test_space_service_smoke(space_service, tmp_path: Path):
    svc = space_service
    name = "demo"

    # ── clean slate ──────────────────────────────────────────────────
    if await svc.get_space(name):
        await svc.delete_space(name)

    # ── create & basic metadata ─────────────────────────────────────
    space = await svc.create_space(
        name=name,
        repository="repo1",
        label="integration",
        owner="rokist",
    )
    assert space.name == name

    got = await svc.get_space(name)
    assert got.label == "integration"

    all_spaces = await svc.list_spaces()
    assert any(s.name == name for s in all_spaces)

    # ── directory ops ───────────────────────────────────────────────
    await svc.create_dir(f"space://{name}/data")
    await svc.create_dir(f"space://{name}/data/raw")

    # ── file write / read / exists / mtime ──────────────────────────
    text = "Hello World"
    await svc.write_file(f"space://{name}/data/hello.txt", text)

    read_back = await svc.read_file(f"space://{name}/data/hello.txt")
    assert read_back == text

    assert await svc.file_exists(f"space://{name}/data/hello.txt")

    mtime = await svc.file_last_modified(f"space://{name}/data/hello.txt")
    assert mtime > 0.0

    # ── move & verify ───────────────────────────────────────────────
    await svc.move_path(
        f"space://{name}/data/hello.txt",
        f"space://{name}/data/raw/world.txt",
    )
    assert await svc.file_exists(f"space://{name}/data/raw/world.txt")

    # ── delete file & directory ─────────────────────────────────────
    await svc.delete_file(f"space://{name}/data/raw/world.txt")
    await svc.delete_dir(f"space://{name}/data/raw")
    assert not await svc.file_exists(f"space://{name}/data/raw/world.txt")

    # ── final cleanup ───────────────────────────────────────────────
    await svc.delete_space(name)
    spaces_after = await svc.list_spaces()
    assert all(s.name != name for s in spaces_after)