import json
import os
from contextlib import contextmanager


@contextmanager
def sink():
    sink_path = os.getenv("SINK_PATH")
    if sink_path is None:
        raise ValueError("SINK_PATH environment variable not set")
    with open(sink_path, "w") as f:
        yield f


def main(inp, context):
    with sink() as f:
        f.write(json.dumps(inp))


def loud(inp, context):
    print(f"!!!I HAVE BEEN CALLED WITH {len(inp)} ITEMS!!!")


def listen(inp, context):
    v = input("enter the value to multiply by number of items: ")
    with sink() as f:
        f.write(str(len(inp) * int(v)))


def panic(inp, context):
    raise ValueError("yanky ho!")


if __name__ == "__main__":
    import sys

    inp = json.loads(sys.argv[1])
    main(inp, {})
