from typing import TypedDict


class PackageDiff(TypedDict):
    package: str
    before: list[str]
    after: list[str]
