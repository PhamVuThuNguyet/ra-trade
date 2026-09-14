"""Filter catalog table rows (PIC, partner, year, essential commodities)."""

from trade_influence.constants import ESSENTIAL_SITC2
from trade_influence.essential import map_baci_hs6_to_sitc2, pad_sitc2

ESSENTIAL_SET = frozenset(ESSENTIAL_SITC2)


def filter_table_rows(
    rows: list[dict],
    *,
    reporters: list[str] | None = None,
    partners: list[str] | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    product_group: str = "all_products",
    source_id: str = "comtrade",
) -> list[dict]:
    """Return rows matching the explorer filter set."""
    selected = rows
    if reporters:
        names = set(reporters)
        selected = [row for row in selected if row.get("country") in names]
    if partners:
        keys = set(partners)
        selected = [row for row in selected if row.get("partner") in keys]
    if year_min is not None:
        selected = [row for row in selected if int(row.get("year", 0)) >= year_min]
    if year_max is not None:
        selected = [row for row in selected if int(row.get("year", 0)) <= year_max]
    if product_group == "essential_commodities":
        selected = [row for row in selected if _is_essential_row(row, source_id)]
    return selected


def _is_essential_row(row: dict, source_id: str) -> bool:
    if "sitc2" in row and row["sitc2"] not in (None, ""):
        return pad_sitc2(row["sitc2"]) in ESSENTIAL_SET
    if source_id == "baci" and row.get("hs6"):
        sitc2 = map_baci_hs6_to_sitc2(row["hs6"])
        return sitc2 in ESSENTIAL_SET if sitc2 else False
    # Index-only rows (no commodity): keep I/E; essential CWI/CWE already filtered
    if row.get("index_id") in {"cwi_essential", "cwe_essential"}:
        return True
    if row.get("index_id") in {"cwi", "cwe"}:
        return False
    if row.get("index_id") in {"import_index", "export_index"}:
        return True
    return False
