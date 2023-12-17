import json
from os import environ

from poetry.console.application import Application as PoetryApplication
from pytest import fixture, mark, skip

from poetry_lock_listener.lock_listener_config import LockListenerConfig, PackageIgnoreSpec
from poetry_lock_listener.plugin import LockListenerPlugin


@fixture()
def lockfile_path(tmp_path):
    return tmp_path / "poetry.lock"


@fixture()
def sink_path(tmp_path):
    ret = tmp_path / "sink"
    environ["SINK_PATH"] = str(ret)
    return ret


@fixture()
def plugin(lockfile_path):
    plugin = LockListenerPlugin()
    plugin.config = LockListenerConfig(
        lock_file_path=str(lockfile_path),
        package_changed_hook="tests.dep_hook:main",
        ignore_packages=[],
    )
    app = PoetryApplication()
    app.auto_exits = False
    plugin.poetry = app.poetry
    return plugin


LOCK_BEFORE = """
        [[package]]
        name = "foo"  # will be removed
        version = "1.0.0"

        [[package]]
        name = "bar"  # will be upgraded
        version = "1.0.0"

        [[package]]
        name = "baz"  # will not change
        version = "1.0.0"

        [metadata]
        lock-version = "2.0"
        """

LOCK_AFTER = """
        [[package]]
        name = "bar"  # upgraded
        version = "2.0.0"

        [[package]]
        name = "baz"  # will not change
        version = "1.0.0"

        [[package]]
        name = "qux"  # new package
        version = "1.0.0"

        [metadata]
        lock-version = "2.0"
        """


@mark.parametrize("run_main", [False, True])
@mark.parametrize("content_hash", [False, True])
def test_simple_flow(plugin, lockfile_path, sink_path, run_main, content_hash):
    if run_main:
        plugin.config.package_changed_hook = "tests/dep_hook.py"

    lockfile_path.write_text(LOCK_BEFORE + ('content-hash = "abc123"' if content_hash else ""))

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER + ('content-hash = "different"' if content_hash else ""))

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "bar",
            "before": ["1.0.0"],
            "after": ["2.0.0"],
        },
        {
            "package": "foo",
            "before": ["1.0.0"],
            "after": [],
        },
        {
            "package": "qux",
            "before": [],
            "after": ["1.0.0"],
        },
    ]


def test_no_command(plugin, lockfile_path, sink_path):
    plugin.config.package_changed_hook = None

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert not sink_path.exists()


@mark.parametrize("lock_before", [False, True])
@mark.parametrize("lock_after", [False, True])
def test_no_lock(plugin, lockfile_path, sink_path, lock_before, lock_after):
    if lock_before and lock_after:
        skip()

    if lock_before:
        lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    if lock_after:
        lockfile_path.write_text(LOCK_AFTER)
    else:
        lockfile_path.unlink(missing_ok=True)

    plugin.post_lock()

    assert not sink_path.exists()


@mark.parametrize("content_hash", [False, True])
def test_no_changes(plugin, lockfile_path, sink_path, content_hash):
    lockfile_path.write_text(LOCK_BEFORE + ('content-hash = "abc123"' if content_hash else ""))

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_BEFORE + ('content-hash = "abc123"' if content_hash else ""))

    plugin.post_lock()

    assert not sink_path.exists()


@mark.parametrize("foo_ignore_version", [None, "1.0.0"])
def test_ignore_foo(plugin, lockfile_path, sink_path, foo_ignore_version):
    plugin.config.ignore_packages = [PackageIgnoreSpec("foo", foo_ignore_version)]

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "bar",
            "before": ["1.0.0"],
            "after": ["2.0.0"],
        },
        {
            "package": "qux",
            "before": [],
            "after": ["1.0.0"],
        },
    ]


def test_ignore_bar_both(plugin, lockfile_path, sink_path):
    plugin.config.ignore_packages = [PackageIgnoreSpec("bar", None)]

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "foo",
            "before": ["1.0.0"],
            "after": [],
        },
        {
            "package": "qux",
            "before": [],
            "after": ["1.0.0"],
        },
    ]


def test_ignore_bar_before(plugin, lockfile_path, sink_path):
    plugin.config.ignore_packages = [PackageIgnoreSpec("bar", "1.0.0")]

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "bar",
            "before": [],
            "after": ["2.0.0"],
        },
        {
            "package": "foo",
            "before": ["1.0.0"],
            "after": [],
        },
        {
            "package": "qux",
            "before": [],
            "after": ["1.0.0"],
        },
    ]


def test_ignore_bar_after(plugin, lockfile_path, sink_path):
    plugin.config.ignore_packages = [PackageIgnoreSpec("bar", "2.0.0")]

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "bar",
            "before": ["1.0.0"],
            "after": [],
        },
        {
            "package": "foo",
            "before": ["1.0.0"],
            "after": [],
        },
        {
            "package": "qux",
            "before": [],
            "after": ["1.0.0"],
        },
    ]


@mark.parametrize("qux_ignore_version", [None, "1.0.0"])
def test_ignore_qux(plugin, lockfile_path, sink_path, qux_ignore_version):
    plugin.config.ignore_packages = [PackageIgnoreSpec("qux", qux_ignore_version)]

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert json.loads(sink_path.read_text()) == [
        {
            "package": "bar",
            "before": ["1.0.0"],
            "after": ["2.0.0"],
        },
        {
            "package": "foo",
            "before": ["1.0.0"],
            "after": [],
        },
    ]

def test_stdout(plugin, lockfile_path, capsys):    
    plugin.config.package_changed_hook = "tests.dep_hook:loud"

    lockfile_path.write_text(LOCK_BEFORE)

    plugin.pre_lock()

    lockfile_path.write_text(LOCK_AFTER)

    plugin.post_lock()

    assert "!!!I HAVE BEEN CALLED WITH 3 ITEMS!!!\n" in capsys.readouterr().out