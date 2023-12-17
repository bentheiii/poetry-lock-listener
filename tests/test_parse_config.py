from poetry_lock_listener.lock_listener_config import LockListenerConfig, PackageIgnoreSpec


def test_parse_config():
    raw = {
        "lockfile": "poetry.lock",
        "package_changed_hook": "foo.py:bar",
        "ignore_packages": [
            "foo",
            {"package": "bar", "version": "1.0.0"},
            {"package": "baz", "version": "*"},
        ],
    }

    config = LockListenerConfig.from_raw(raw)
    assert config.lock_file_path == "poetry.lock"
    assert config.package_changed_hook == "foo.py:bar"
    assert config.ignore_packages == [
        PackageIgnoreSpec("foo", None),
        PackageIgnoreSpec("bar", "1.0.0"),
        PackageIgnoreSpec("baz", None),
    ]


def test_parse_config_empty():
    raw = {}

    config = LockListenerConfig.from_raw(raw)
    assert config.lock_file_path is None
    assert config.package_changed_hook is None
    assert config.ignore_packages == []
