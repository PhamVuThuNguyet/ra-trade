"""Repository locations.

Analysis packages live under ``src/`` and are imported by their existing names
(``baci``, ``trade_influence``, …). Raw extracts, outputs, and reports stay at
the repository root.
"""

from pathlib import Path


def _find_project_root() -> Path:
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("Could not locate repository root (pyproject.toml).")


PROJECT_ROOT = _find_project_root()
SRC_DIR = Path(__file__).resolve().parent
