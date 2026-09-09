"""Write explorer-tool/public/data/catalog.json from study outputs and labelled mock series.

Thin wrapper around ``explorer_catalog.build.write_catalog``.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
EXPLORER_TOOL = PROJECT_ROOT / "explorer-tool"
if str(EXPLORER_TOOL) not in sys.path:
    sys.path.insert(0, str(EXPLORER_TOOL))

from explorer_catalog.build import write_catalog


def main() -> None:
    path = write_catalog()
    print("Explorer catalog export complete.")
    print(f"Catalog: {path}")


if __name__ == "__main__":
    main()
