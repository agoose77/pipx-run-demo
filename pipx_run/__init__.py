# SPDX-FileCopyrightText: 2022-present Angus Hollands <goosey15@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import io
import re
import toml
import build
import tempfile
import string
import pathlib
import dataclasses
import subprocess


@dataclasses.dataclass
class Script:
    metadata: dict
    content: str


def parse_script_metadata(source: io.TextIOBase) -> Script:    
    header = []
    content = []

    for line in source:
        if not header and line.startswith("#!"):
            continue
        if not line.startswith("#"):
            content.append(line)
            break
        header.append(line.lstrip("#"))
    content.extend(source)

    header = "\n".join(header)
    metadata_content = toml.loads(header)

    metadata = {
        "project": metadata_content
    }

    return Script(metadata, "".join(content))



def sanitise_script_name(name: str) -> str:
    for char in string.punctuation + string.whitespace:
        name = name.replace(char, "_")

    # Do we have an identifier
    if re.match(r"[a-zA-Z_].*", name):
        return name
    return f"script_{name}"

    

def get_build_backend_config():
    return {
        "build-system": {
            "requires": ["hatchling"],
            "build-backend": "hatchling.build"
        }
    }


SCRIPT_TEMPLATE = """
def main():
    exec({content!r})
"""


@dataclasses.dataclass
class ExecutableWheel:
    script_name: str
    wheel_path: pathlib.Path


def build_wheel(script: Script, default_name="script-the-world 3"):
    path = pathlib.Path(tempfile.mkdtemp())

    pyproject_path = path / "pyproject.toml"

    config = script.metadata.copy()
    project_config = config["project"]

    if "name" not in config:
        project_config['name'] = sanitise_script_name(default_name)

    if "version" not in config:
        project_config['version'] = "0.0.1"

    config.update(
        get_build_backend_config()
    )

    name = project_config['name']
    module_name = sanitise_script_name(name)

    script_path = path / f"{module_name}.py"
    script_path.write_text(
        SCRIPT_TEMPLATE.format(
            content=script.content
        )
    )
    
    project_config['scripts'] = {
        name: f"{module_name}:main"
    }

    with open(pyproject_path, "w") as f:
        toml.dump(config, f)

    builder = build.ProjectBuilder(path)

    wheel_path = pathlib.Path(
        builder.build("wheel", path)
    )
    return ExecutableWheel(module_name, wheel_path)
