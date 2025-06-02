from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import darca_space_manager.config as cfg
import darca_space_manager.metaspace.yaml_metaspace_backend as ymb


def _utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


def _patch_directories(tmp: Path, monkeypatch):
    base = tmp / "spaces"
    monkeypatch.setattr(
        cfg,
        "get_directories",
        lambda: {
            "SPACE_DIR": str(base),
            "METADATA_DIR": str(tmp),  # unused but satisfies callers
            "CONTROL_DIR": str(tmp / "ctrl"),
            "LOG_DIR": str(tmp / "log"),
        },
    )
    monkeypatch.setattr(ymb, "REGISTRY_FILE", str(tmp / "spaces_registry.yaml"))


def _backend(tmp_path, monkeypatch) -> ymb.YamlMetaspaceBackend:
    _patch_directories(tmp_path, monkeypatch)
    return ymb.YamlMetaspaceBackend()


def test_add_get_list_rename_remove(monkeypatch, tmp_path):
    back = _backend(tmp_path, monkeypatch)

    back.add_space("demo", label="test", repository="repo1", owner="u")
    assert back.get_space("demo")["label"] == "test"
    assert len(back.list_spaces()) == 1

    # field setters
    back.set_label("demo", "prod")
    assert back.get_space("demo")["label"] == "prod"

    back.touch("demo")
    lm = datetime.fromisoformat(back.get_space("demo")["last_modified_at"])
    assert (datetime.now(timezone.utc) - lm).total_seconds() < 2

    # rename
    back.rename_space("demo", "demo2")
    assert back.get_space("demo2")["name"] == "demo2"

    # remove
    back.remove_space("demo2")
    assert back.list_spaces() == []


def test_save_reload(monkeypatch, tmp_path):
    back = _backend(tmp_path, monkeypatch)
    back.add_space("s1", repository="repo1")
    back.save_registry()

    # make sure a new instance loads existing data
    back2 = _backend(tmp_path, monkeypatch)
    assert back2.get_space("s1")["name"] == "s1"
