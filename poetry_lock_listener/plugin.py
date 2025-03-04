from collections.abc import Mapping
from enum import IntEnum
from os import getenv
from pathlib import Path
from sys import stdin, stdout
from typing import Any

import tomli
from cleo.events.console_events import COMMAND, TERMINATE
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from poetry.plugins import ApplicationPlugin
from poetry.poetry import Poetry
from poetry.utils.env import EnvManager

from poetry_lock_listener._version import __version__
from poetry_lock_listener.lock_listener_config import LockListenerConfig
from poetry_lock_listener.lock_spec import LockSpec
from poetry_lock_listener.util import get_fd


class Verbosity(IntEnum):
    SILENT = 0
    NORMAL = 1
    VERBOSE = 2
    VERY_VERBOSE = 3
    DEBUG = 4


class LockListenerPlugin(ApplicationPlugin):
    locked_before: LockSpec | None = None
    config: LockListenerConfig | None
    poetry: Poetry
    verbosity: Verbosity

    def print(self, verbosity: Verbosity, *args: Any, **kwargs: Any) -> None:
        if self.verbosity > verbosity:
            print("Poetry Lock Listener: ", *args, **kwargs)  # noqa: T201

    def activate(self, application: Application) -> None:
        self.poetry = application.poetry
        self.verbosity = Verbosity.NORMAL
        raw_verbosity = getenv("POETRY_LOCK_LISTENER_VERBOSITY")
        if raw_verbosity is not None:
            try:
                self.verbosity = Verbosity(int(raw_verbosity))
            except ValueError:
                self.print(Verbosity.SILENT, f"Invalid verbosity level: {raw_verbosity!r}")
        self.print(Verbosity.VERBOSE, f"Verbosity level {self.verbosity}, version {__version__}")
        self.config = self._get_config(self.poetry)

        if self.config is None:
            # the tool is not configured for this project
            self.print(Verbosity.VERBOSE, "No configuration found")
            return
        event_dispatcher = application.event_dispatcher
        if event_dispatcher is None:
            self.print(Verbosity.NORMAL, "No event dispatcher found, lock listener will not work")
            return
        event_dispatcher.add_listener(COMMAND, self.on_command)
        event_dispatcher.add_listener(TERMINATE, self.on_terminate)

    def _get_config(self, poetry: Poetry) -> LockListenerConfig | None:
        pyproject: Mapping[str, Any]
        try:
            pyproject = poetry.pyproject.data
        except Exception:
            with Path("pyproject.toml").open("rb") as f:
                pyproject = tomli.load(f)

        raw = pyproject.get("tool", {}).get("poetry_lock_listener", None)
        if raw is None:
            return None
        return LockListenerConfig.from_raw(raw)

    def on_command(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
        self.print(Verbosity.DEBUG, "Running pre-command")
        self.pre_lock()

    def pre_lock(self) -> None:
        assert self.config is not None
        # we need to get the lockfile path before the lock command is executed
        # because the lock command will update the lock file
        try:
            with Path(self.config.lock_file_path or "poetry.lock").open("rb") as f:
                locked_before_raw = tomli.load(f)
        except FileNotFoundError:
            # lockfile doesn't exist
            self.print(Verbosity.VERBOSE, "Lockfile doesn't exist before command")
            self.locked_before = None
        else:
            try:
                self.locked_before = LockSpec.from_raw(locked_before_raw)
            except Exception as e:
                self.print(Verbosity.NORMAL, f"Failed to parse lockfile: {e!r}")
                return
            else:
                self.locked_before.apply_ignores(self.config.ignore_packages)

    def on_terminate(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
        self.print(Verbosity.DEBUG, "Running pos-command")
        self.post_lock()

    def post_lock(self) -> None:
        assert self.config is not None
        if self.locked_before is None:
            # this means the lockfile didn't exist before the lock command was run
            return

        try:
            with Path(self.config.lock_file_path or "poetry.lock").open("rb") as f:
                locked_after_raw = tomli.load(f)
        except FileNotFoundError:
            # lockfile doesn't exist
            self.print(Verbosity.VERBOSE, "Lockfile doesn't exist after command")
            return

        try:
            locked_after = LockSpec.from_raw(locked_after_raw)
        except Exception as e:
            self.print(Verbosity.NORMAL, f"Failed to parse lockfile: {e!r}")
            return
        locked_after.apply_ignores(self.config.ignore_packages)

        diff = LockSpec.diff(self.locked_before, locked_after)
        if not diff:
            # no packages changed
            self.print(Verbosity.VERBOSE, "No packages changed")
            return
        env_manager = EnvManager(self.poetry)
        env = env_manager.create_venv()
        cb_command = self.config.get_callback_command(diff)
        if cb_command is None:
            self.print(Verbosity.NORMAL, "No callback command was configured")
            return
        subprocess_stdin = get_fd(stdin)
        if subprocess_stdin is None:
            self.print(Verbosity.NORMAL, "proccess STDIN cannot be redirected, hook might not work properly")
        subprocess_stdout = get_fd(stdout)
        if subprocess_stdout is None:
            self.print(Verbosity.NORMAL, "proccess STDOUT cannot be redirected, hook might not work properly")

        try:
            env.run(*cb_command, call=True, stdin=subprocess_stdin, stdout=subprocess_stdout)
        except Exception as e:
            self.print(Verbosity.NORMAL, f"Failed to run callback command: {e!r}")
            return
