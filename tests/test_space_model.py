from darca_space_manager.models.space import Space
from datetime import datetime, timezone


def test_space_model_fields():
    now = datetime.now(timezone.utc)

    space = Space(
        name="foo",
        path="/tmp/foo",
        label="unit",
        created_at=now,
        last_modified_at=now,
    )

    assert space.name == "foo"
    assert space.label == "unit"
    assert space.created_at == now
    assert space.to_dict()["path"] == "/tmp/foo"
