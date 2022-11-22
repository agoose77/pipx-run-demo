import argparse
import dataclasses
import subprocess
import os.path
from . import build_wheel, parse_script_metadata


@dataclasses.dataclass
class NamedFile:
    name: str
    file: object


def parse_file_name(path):
    if path == "-":
        return NamedFile("-", sys.stdin)
    precursor, ext = os.path.splitext(path) 
    name = os.path.basename(precursor)
    return NamedFile(name, open(path, "r"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=parse_file_name)
    args, remainder = parser.parse_known_args()

    metadata = parse_script_metadata(args.script.file)
    result = build_wheel(metadata, args.script.name)

    subprocess.run([
        "pipx", "run", "--spec", result.wheel_path, result.script_name, *remainder
    ])


if __name__ == "__main__":
    main()
