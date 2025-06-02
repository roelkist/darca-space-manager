# tests/test_space_service.py
# License: MIT

import pytest
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
