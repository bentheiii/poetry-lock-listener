from dataclasses import dataclass
from typing import Any


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


@dataclass
class LockListenerConfig:
    lock_file_path: str | None
    package_changed_hook: str | None
    ignore_packages: list[PackageIgnoreSpec]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "LockListenerConfig":
        return cls(
            lock_file_path=raw.get("lockfile", None),
            package_changed_hook=raw.get("package_changed_hook", None),
            ignore_packages=[PackageIgnoreSpec.from_raw(raw_ignore) for raw_ignore in raw.get("ignore_packages", ())],
        )

    def get_callback_command(self, encoded_input: str) -> list[str] | None:
        if self.package_changed_hook is None:
            return None
        file, _, func = self.package_changed_hook.partition(":")
        ret = ["python"]
        if func:
            ret.extend(
                [
                    "-c",
                    f"from {file} import {func}; import json; import sys; {func}(json.loads(sys.argv[1]))",
                    encoded_input,
                ]
            )
        else:
            ret.extend([file, encoded_input])
        return ret
