from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from warnings import warn

from poetry_lock_listener.lock_diff import PackageDiff
from poetry_lock_listener.lock_listener_config import PackageIgnoreSpec


@dataclass
class LockSpec:
    # mapping a package name to a sorted list of versions described in its lockfile, in some cases,
    # there may be more than one version listed for a package depending on the system and python
    # version. Since this not normally expected (especially since this plugin is designed for services)
    # we're not gonna put a lot of effort into parsing these cases
    packages: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> LockSpec:
        lock_version = raw.get("metadata", {}).get("lock-version", None)
        if lock_version is None:
            warn("No lock version found, treating as v2")
            return cls.from_raw_v2(raw)

        if isinstance(lock_version, str) and lock_version.startswith("2."):
            return cls.from_raw_v2(raw)
        else:
            warn(f"Unsupported lock version: {lock_version!r}, treating as v2")
            return cls.from_raw_v2(raw)

    @classmethod
    def from_raw_v2(cls, raw: dict[str, Any]) -> LockSpec:
        packages: dict[str, list[str]] = {}
        for package in raw.get("package", ()):
            name = package.get("name")
            version = package.get("version")
            if name is None or version is None:
                continue
            packages.setdefault(name, []).append(version)
        for v in packages.values():
            v.sort()
        return cls(packages)

    def apply_ignores(self, ignores: list[PackageIgnoreSpec]) -> None:
        for ignore in ignores:
            if ignore.package in self.packages:
                if ignore.version:
                    self.packages[ignore.package] = [v for v in self.packages[ignore.package] if v != ignore.version]
                else:
                    del self.packages[ignore.package]

    @classmethod
    def diff(cls, before: LockSpec, after: LockSpec) -> list[PackageDiff]:
        packages = set(before.packages) | set(after.packages)
        ret = []
        for package in sorted(packages):
            before_versions = before.packages.get(package, [])
            after_versions = after.packages.get(package, [])
            if before_versions == after_versions:
                continue
            diff = PackageDiff(package=package, before=before_versions, after=after_versions)
            ret.append(diff)
        return ret
