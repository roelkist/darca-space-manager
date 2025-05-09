import pytest
from darca_space_manager.models.space_uri import SpaceURI
from darca_space_manager.api.space_file_manager import SpaceFileManagerException


def test_parse_valid_space_uri():
    uri = SpaceURI.from_str("space://project/config.yaml")
    assert uri.space == "project"
    assert uri.path == "config.yaml"
    assert str(uri) == "space://project/config.yaml"


def test_parse_invalid_scheme():
    with pytest.raises(ValueError, match="Invalid URI scheme"):
        SpaceURI.from_str("http://project/file.txt")


def test_parse_missing_path():
    with pytest.raises(ValueError, match="Invalid space URI format"):
        SpaceURI.from_str("space://project")


def test_to_string_roundtrip():
    original = "space://alpha/data.yaml"
    uri = SpaceURI.from_str(original)
    assert str(uri) == original
