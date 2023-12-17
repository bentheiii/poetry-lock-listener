from pytest import mark

from poetry_lock_listener.lock_spec import LockSpec


@mark.parametrize("version", ["2.0", "1.0", None])
def test_parse(version):
    raw = {
        "metadata": {
            "lock-version": version,
            "content-hash": "abc123",
        },
        "package": [
            {
                "name": "foo",
                "version": "1.0.0",
            },
            {
                "name": "foo",
                "version": "1.0.1",
            },
            {
                "name": "bar",
                "version": "1.0.0",
            },
            {
                "version": "1.0.0",
            },
            {
                "name": "qux",
            },
            {},
        ],
    }

    spec = LockSpec.from_raw(raw)
    assert spec == LockSpec(
        content_hash="abc123",
        packages={
            "foo": ["1.0.0", "1.0.1"],
            "bar": ["1.0.0"],
        },
    )
