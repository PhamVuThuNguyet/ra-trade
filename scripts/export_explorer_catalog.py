"""Write explorer-tool/public/data/catalog.json from study outputs and labelled mock series.

Thin wrapper around ``explorer_catalog.build.write_catalog``.
"""

from _bootstrap import add_src_to_path

add_src_to_path()

from explorer_catalog.build import write_catalog


def main() -> None:
    path = write_catalog()
    print("Explorer catalog export complete.")
    print(f"Catalog: {path}")


if __name__ == "__main__":
    main()
