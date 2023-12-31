from typing import IO, TypeVar

T = TypeVar("T", bound=IO)


def get_fd(x: T) -> int | None:
    try:
        return x.fileno()
    except OSError:
        return None
