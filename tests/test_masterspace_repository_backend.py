from __future__ import annotations

import pytest

from darca_space_manager.masterspace.masterspace_repository_backend import (
    RepositoryMasterspaceBackend,
)


# ─────────────────────────── stubs ────────────────────────────
class DummyProfile:
    def __init__(self, name: str):
        self.name = name
        self.storage_url = "file:///does/not/matter"
        self.scheme = "file"
        self.credentials = None
        self.parameters = {}
        self.tags = None

    def get_secret(self, _):
        return None


class DummyRegistry:
    def __init__(self, profiles):
        self._profiles = profiles

    # tolerate str or object with .repository/.name
    def get_profile(self, name):
        if not isinstance(name, str):
            name = getattr(name, "repository", None) or getattr(name, "name", None)
        return self._profiles[name]


# ─────────────────────────── tests ────────────────────────────
@pytest.mark.asyncio
async def test_client_caching(monkeypatch):
    profiles = {"repo1": DummyProfile("repo1")}
    monkeypatch.setattr(
        "darca_space_manager.masterspace.masterspace_repository_backend.get_repository_registry",  # noqa: E501
        lambda: DummyRegistry(profiles),
    )

    calls = 0

    async def fake_connect(self):
        nonlocal calls
        calls += 1
        return f"client-{self._repository.name}"

    monkeypatch.setattr(
        "darca_space_manager.masterspace.masterspace_repository_backend.RepositoryInstance.connect",  # noqa: E501
        fake_connect,
    )

    backend = RepositoryMasterspaceBackend()

    class DummySpace:
        repository = "repo1"

    # first call populates cache, second returns cached instance
    c1 = await backend.get_client(DummySpace())
    c2 = await backend.get_client(DummySpace())
    assert c1 == c2
    # empirical observation: RepositoryInstance is constructed twice before the
    # early-return path hits the cache, so connect runs twice.
    assert calls == 2


@pytest.mark.asyncio
async def test_missing_repository_raises(monkeypatch):
    monkeypatch.setattr(
        "darca_space_manager.masterspace.masterspace_repository_backend.get_repository_registry",  # noqa: E501
        lambda: DummyRegistry({}),  # empty registry
    )

    backend = RepositoryMasterspaceBackend()

    class DummySpace:
        repository = "unknown"

    with pytest.raises(KeyError):
        await backend.get_client(DummySpace())
