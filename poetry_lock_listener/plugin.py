import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from warnings import warn
import subprocess

import tomli
from cleo.events.console_events import COMMAND, TERMINATE
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from poetry.plugins import ApplicationPlugin
from poetry.poetry import Poetry
from poetry.utils.env import EnvManager

from poetry_lock_listener.lock_listener_config import LockListenerConfig
from poetry_lock_listener.lock_spec import LockSpec


class LockListenerPlugin(ApplicationPlugin):
    locked_before: LockSpec | None = None
    config: LockListenerConfig | None
    poetry: Poetry

    def activate(self, application: Application) -> None:
        self.poetry = application.poetry
        self.config = self._get_config(application)

        if self.config is None:
            # the tool is not configured for this project
            return
        event_dispatcher = application.event_dispatcher
        if event_dispatcher is None:
            warn("No event dispatcher found, lock listener will not work")
            return
        event_dispatcher.add_listener(COMMAND, self.on_command)
        event_dispatcher.add_listener(TERMINATE, self.on_terminate)

    @classmethod
    def _get_config(cls, application: Application) -> LockListenerConfig | None:
        pyproject: Mapping[str, Any]
        try:
            pyproject = application.poetry.pyproject.data
        except Exception:
            with Path("pyproject.toml").open("rb") as f:
                pyproject = tomli.load(f)

        raw = pyproject.get("tool", {}).get("poetry_lock_listener", None)
        if raw is None:
            return None
        return LockListenerConfig.from_raw(raw)

    def on_command(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
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
            self.locked_before = None
        else:
            try:
                self.locked_before = LockSpec.from_raw(locked_before_raw)
            except Exception as e:
                warn(f"Failed to parse lockfile: {e!r}")
                return
            else:
                self.locked_before.apply_ignores(self.config.ignore_packages)

    def on_terminate(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
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
            return

        after_content_hash = locked_after_raw.get("metadata", {}).get("content-hash", None)
        if after_content_hash == self.locked_before.content_hash and after_content_hash is not None:
            # either content hashes are the same, lockfile was not changed
            # or a lockfile was doesn't have a content hash
            return

        try:
            locked_after = LockSpec.from_raw(locked_after_raw)
        except Exception as e:
            warn(f"Failed to parse lockfile: {e!r}")
            return
        locked_after.apply_ignores(self.config.ignore_packages)

        diff = LockSpec.diff(self.locked_before, locked_after)
        if not diff:
            # no packages changed
            return
        env_manager = EnvManager(self.poetry)
        env = env_manager.create_venv()
        input_buffer = json.dumps(diff)
        cb_command = self.config.get_callback_command(input_buffer)
        if cb_command is None:
            warn("No callback command was configured")
            return
        try:
            output = env.run(*cb_command)
        except Exception as e:
            warn(f"Failed to run callback command: {e!r}")
            return
        if output:
            print(output)
