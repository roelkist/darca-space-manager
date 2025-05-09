from darca_space_manager.core.space_registry import SpaceMetadataRegistry


def test_add_and_remove_space(darca_base_env):
    registry = SpaceMetadataRegistry()

    space = {
        "name": "alpha",
        "path": f"{darca_base_env}/alpha",
        "label": "test",
        "created_at": "2025-01-01T00:00:00Z",
        "last_modified_at": "2025-01-01T00:00:00Z",
    }

    registry.add_space("alpha", space)
    assert registry.get_space("alpha")["name"] == "alpha"

    registry.remove_space("alpha")
    assert registry.get_space("alpha") is None
