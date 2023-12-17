import json
import os


def main(inp):
    sink_path = os.getenv("SINK_PATH")
    if sink_path is None:
        raise ValueError("SINK_PATH environment variable not set")
    with open(sink_path, "w") as f:
        f.write(json.dumps(inp))


def loud(inp):
    print(f"!!!I HAVE BEEN CALLED WITH {len(inp)} ITEMS!!!")


if __name__ == "__main__":
    import sys

    inp = json.loads(sys.argv[1])
    main(inp)
