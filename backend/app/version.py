"""App version information."""

import tomllib
from pathlib import Path

try:
    # Try importlib.metadata first
    from importlib.metadata import version as get_version
    __version__ = get_version("app")
except Exception:
    # Fallback: read from pyproject.toml
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        __version__ = data["project"]["version"]
    except Exception:
        __version__ = "0.1.0"
