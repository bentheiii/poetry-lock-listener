import json
from dataclasses import dataclass
from typing import Any, Protocol, Self


@dataclass(frozen=True)
class PackageIgnoreSpec:
    package: str
    version: str | None

    @classmethod
    def from_raw(cls, raw: Any) -> "PackageIgnoreSpec":
        if isinstance(raw, str):
            return cls(raw, None)
        version = raw.get("version", None)
        if version == "*":
            version = None
        return cls(raw["package"], version)


class Hook(Protocol):
    def get_subprocess_args(self, diff: Any, context: Any) -> list[str]: ...


@dataclass(frozen=True)
class PyFileHook(Hook):
    file: str

    def get_subprocess_args(self, diff: Any, context: Any) -> list[str]:
        return ["python", self.file, json.dumps(diff), json.dumps(context)]


@dataclass(frozen=True)
class PyFunctionHook(Hook):
    file: str
    func: str

    @classmethod
    def from_raw(cls, raw: Any) -> Self:
        file, _, func = raw.partition(":")
        if not func:
            raise ValueError("func must be in the format 'file:func'")
        return cls(file, func)

    def get_subprocess_args(self, diff: Any, context: Any) -> list[str]:
        return [
            "python",
            "-c",
            f"from {self.file} import {self.func}; import json; import sys; {self.func}(json.loads(sys.argv[1]), json.loads(sys.argv[2]))",
            json.dumps(diff),
            json.dumps(context),
        ]


@dataclass(frozen=True)
class ExecHook(Hook):
    command: str

    def get_subprocess_args(self, diff: Any, context: Any) -> list[str]:
        ret = self.command.split(" ")
        ret.extend([json.dumps(diff), json.dumps(context)])
        return ret


def get_hook(raw: Any) -> Hook:
    if isinstance(raw, str):
        if ":" in raw:
            return PyFunctionHook.from_raw(raw)
        return PyFileHook(raw)
    if isinstance(raw, dict):
        if "exec" in raw:
            return ExecHook(raw["exec"])
        elif "func" in raw:
            return PyFunctionHook.from_raw(raw["func"])
        elif "file" in raw:
            return PyFileHook(raw["file"])
    raise ValueError(f"Invalid hook: {raw}")


@dataclass
class LockListenerConfig:
    lock_file_path: str | None
    package_changed_hook: Hook | None
    ignore_packages: list[PackageIgnoreSpec]
    hook_context: Any

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "LockListenerConfig":
        raw_hook = raw.get("package_changed_hook")
        if raw_hook is not None:
            package_changed_hook = get_hook(raw_hook)
        else:
            package_changed_hook = None
        return cls(
            lock_file_path=raw.get("lockfile"),
            package_changed_hook=package_changed_hook,
            ignore_packages=[PackageIgnoreSpec.from_raw(raw_ignore) for raw_ignore in raw.get("ignore_packages", ())],
            hook_context=raw.get("hook_context", {}),
        )

    def get_callback_command(self, diff: Any) -> list[str] | None:
        if self.package_changed_hook is None:
            return None
        return self.package_changed_hook.get_subprocess_args(diff, self.hook_context)
