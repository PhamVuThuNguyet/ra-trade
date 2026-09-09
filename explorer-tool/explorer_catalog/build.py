"""Build explorer-tool/public/data/catalog.json from study CSVs and labelled mock services."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from explorer_catalog.constants import (
    BACI_OUTPUT_CSV_DIR,
    BACI_VINTAGE,
    COMTRADE_VINTAGE,
    DEFAULT_CATALOG_PATH,
    ESSENTIAL_DIVISIONS,
    INDEX_CWE,
    INDEX_CWE_ESSENTIAL,
    INDEX_CWI,
    INDEX_CWI_ESSENTIAL,
    INDEX_EXPORT,
    INDEX_IMPORT,
    OUTPUT_CSV_DIR,
    PARTNER_DISPLAY,
    PARTNER_PLOT_COLORS,
    SOURCE_BACI,
    SOURCE_COMTRADE,
    SOURCE_DISPLAY,
    UI_FLAGS,
)
from explorer_catalog.mock_services import mock_service_tables
from explorer_catalog.overlay import load_overlay
from trade_influence.constants import INDEX_DISPLAY


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _points_from_wide(
    frame: pd.DataFrame,
    source_id: str,
    provenance: str,
    column_to_index: dict[str, str],
) -> list[dict]:
    if frame.empty:
        return []
    points: list[dict] = []
    for _, row in frame.iterrows():
        for col, index_id in column_to_index.items():
            if col not in frame.columns:
                continue
            value = row[col]
            points.append(
                {
                    "source_id": source_id,
                    "country": str(row["country"]),
                    "year": int(row["year"]),
                    "partner": str(row["partner"]),
                    "index_id": index_id,
                    "value": None if pd.isna(value) else float(value),
                    "provenance": provenance,
                }
            )
    return points


def _table_from_points(
    points: list[dict],
    source_id: str,
    data_type_id: str,
    product_group_id: str,
    provenance: str,
    vintage: str | None,
) -> dict:
    rows = [
        p
        for p in points
        if p["source_id"] == source_id
        and (
            product_group_id != "essential_commodities"
            or p["index_id"]
            in {
                INDEX_IMPORT,
                INDEX_EXPORT,
                INDEX_CWI_ESSENTIAL,
                INDEX_CWE_ESSENTIAL,
            }
        )
        and (
            product_group_id != "all_products"
            or p["index_id"]
            in {INDEX_IMPORT, INDEX_EXPORT, INDEX_CWI, INDEX_CWE}
        )
    ]
    return {
        "source_id": source_id,
        "data_type_id": data_type_id,
        "product_group_id": product_group_id,
        "provenance": provenance,
        "vintage": vintage,
        "columns": ["country", "year", "partner", "index_id", "value"],
        "rows": rows,
    }


def _load_goods_points(baci_csv: Path, comtrade_csv: Path) -> list[dict]:
    points: list[dict] = []
    baci = _read_csv(baci_csv / "indices_baci.csv")
    points.extend(
        _points_from_wide(
            baci,
            SOURCE_BACI,
            "study_output",
            {
                INDEX_IMPORT: INDEX_IMPORT,
                INDEX_EXPORT: INDEX_EXPORT,
                INDEX_CWI: INDEX_CWI,
                INDEX_CWE: INDEX_CWE,
            },
        )
    )
    for name, index_id in (
        ("cwi_essential_baci.csv", INDEX_CWI_ESSENTIAL),
        ("cwe_essential_baci.csv", INDEX_CWE_ESSENTIAL),
    ):
        extra = _read_csv(baci_csv / name)
        col = INDEX_CWI if "cwi" in name else INDEX_CWE
        points.extend(
            _points_from_wide(extra, SOURCE_BACI, "study_output", {col: index_id})
        )
    comtrade = _read_csv(comtrade_csv / "indices_comtrade.csv")
    points.extend(
        _points_from_wide(
            comtrade,
            SOURCE_COMTRADE,
            "study_output",
            {
                INDEX_IMPORT: INDEX_IMPORT,
                INDEX_EXPORT: INDEX_EXPORT,
                INDEX_CWI: INDEX_CWI,
                INDEX_CWE: INDEX_CWE,
            },
        )
    )
    for name, index_id in (
        ("cwi_essential_comtrade.csv", INDEX_CWI_ESSENTIAL),
        ("cwe_essential_comtrade.csv", INDEX_CWE_ESSENTIAL),
    ):
        extra = _read_csv(comtrade_csv / name)
        col = INDEX_CWI if "cwi" in name else INDEX_CWE
        points.extend(
            _points_from_wide(
                extra, SOURCE_COMTRADE, "study_output", {col: index_id}
            )
        )
    return points


def prefer_study_output(points: list[dict]) -> list[dict]:
    """Drop mock goods-trade index points when a study_output point exists."""
    study_keys = {
        (p["source_id"], p["country"], p["year"], p["partner"], p["index_id"])
        for p in points
        if p["provenance"] == "study_output"
    }
    kept: list[dict] = []
    for point in points:
        key = (
            point["source_id"],
            point["country"],
            point["year"],
            point["partner"],
            point["index_id"],
        )
        if point["provenance"] == "mock" and key in study_keys:
            continue
        kept.append(point)
    return kept


def build_catalog(
    *,
    baci_csv: Path = BACI_OUTPUT_CSV_DIR,
    comtrade_csv: Path = OUTPUT_CSV_DIR,
    overlay_csv_dir: Path | None = None,
    calendar_fallback: bool = True,
) -> dict:
    points = prefer_study_output(_load_goods_points(baci_csv, comtrade_csv))
    goods_provenance = "study_output" if points else "mock"
    tables = [
        _table_from_points(
            points, SOURCE_BACI, "goods_trade", "all_products", goods_provenance, BACI_VINTAGE
        ),
        _table_from_points(
            points,
            SOURCE_BACI,
            "goods_trade",
            "essential_commodities",
            goods_provenance,
            BACI_VINTAGE,
        ),
        _table_from_points(
            points,
            SOURCE_COMTRADE,
            "goods_trade",
            "all_products",
            goods_provenance,
            COMTRADE_VINTAGE,
        ),
        _table_from_points(
            points,
            SOURCE_COMTRADE,
            "goods_trade",
            "essential_commodities",
            goods_provenance,
            COMTRADE_VINTAGE,
        ),
        *mock_service_tables(),
    ]
    return {
        "generated_from": {
            "note": "Study CSVs plus explorer_catalog/mock; not an analysis artifact",
            "baci_vintage": BACI_VINTAGE,
            "comtrade_vintage": COMTRADE_VINTAGE,
        },
        "sources": [
            {"id": SOURCE_BACI, "display_name": SOURCE_DISPLAY[SOURCE_BACI], "vintage": BACI_VINTAGE},
            {
                "id": SOURCE_COMTRADE,
                "display_name": SOURCE_DISPLAY[SOURCE_COMTRADE],
                "vintage": COMTRADE_VINTAGE,
            },
        ],
        "data_types": [
            {
                "id": "goods_trade",
                "display_name": "Goods trade",
                "provenance_default": "study_output",
            },
            {
                "id": "services",
                "display_name": "Services",
                "provenance_default": "mock",
            },
        ],
        "product_groups": [
            {"id": "all_products", "display_name": "All products"},
            {"id": "essential_commodities", "display_name": "Essential commodities"},
        ],
        "partners": [
            {
                "id": key,
                "display_name": PARTNER_DISPLAY[key],
                "plot_color": PARTNER_PLOT_COLORS[key],
            }
            for key in PARTNER_DISPLAY
        ],
        "essential_divisions": list(ESSENTIAL_DIVISIONS),
        "index_display": dict(INDEX_DISPLAY),
        "ui": dict(UI_FLAGS),
        "tables": tables,
        "index_series": points,
        "overlay": load_overlay(
            csv_dir=overlay_csv_dir,
            calendar_fallback=calendar_fallback,
        ),
    }


def write_catalog(path: Path = DEFAULT_CATALOG_PATH, **kwargs) -> Path:
    catalog = build_catalog(**kwargs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return path
