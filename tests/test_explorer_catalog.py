"""Tests for explorer catalog isolation, schema, filters, overlay, and provenance."""

import ast
from pathlib import Path

import pandas as pd
import pytest

from explorer_catalog.build import build_catalog, prefer_study_output, write_catalog
from explorer_catalog.constants import DEFAULT_CATALOG_PATH, GOODS_TRADE_INDEX_IDS
from explorer_catalog.filters import filter_table_rows
from explorer_catalog.overlay import load_overlay
from project_paths import PROJECT_ROOT, SRC_DIR

ANALYSIS_PACKAGES = (
    "baci",
    "baci_characteristics",
    "comtrade_characteristics",
    "comtrade_download",
    "event_context",
    "trade_anomaly",
    "trade_discrepancy",
    "trade_influence",
)
BANNED_IMPORTS = ("explorer_catalog", "explorer_tool")
SCHEMA_REQUIRED = (
    "generated_from",
    "sources",
    "data_types",
    "product_groups",
    "partners",
    "index_display",
    "essential_divisions",
    "tables",
    "index_series",
    "overlay",
    "ui",
)


def _assert_no_banned_imports(package_dir: Path) -> None:
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        assert "explorer-tool" not in text
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(BANNED_IMPORTS)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(BANNED_IMPORTS)


def test_catalog_package_lives_under_src():
    catalog = SRC_DIR / "explorer_catalog" / "build.py"
    leftover_root = PROJECT_ROOT / "explorer_catalog"
    leftover_ui = PROJECT_ROOT / "explorer-tool" / "explorer_catalog"
    assert catalog.is_file()
    assert not leftover_root.exists()
    assert not leftover_ui.exists()


def test_analysis_packages_do_not_import_explorer_surfaces():
    for name in ANALYSIS_PACKAGES:
        _assert_no_banned_imports(SRC_DIR / name)


def test_overlay_module_does_not_fetch_remote():
    source = (SRC_DIR / "explorer_catalog" / "overlay.py").read_text(
        encoding="utf-8"
    )
    assert "fetch_remote" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "requests" not in source


def _write_index_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2013,
                "partner": "aus",
                "import_index": 0.4,
                "export_index": 0.2,
                "cwi": 0.1,
                "cwe": 0.05,
            }
        ]
    ).to_csv(path, index=False)


def _write_essential_csv(path: Path, column: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"country": "Fiji", "year": 2013, "partner": "aus", column: 0.08}]
    ).to_csv(path, index=False)


def _build_fixture_catalog(tmp_path: Path, **kwargs) -> dict:
    baci_csv = tmp_path / "baci"
    comtrade_csv = tmp_path / "comtrade"
    _write_index_csv(baci_csv / "indices_baci.csv")
    _write_index_csv(comtrade_csv / "indices_comtrade.csv")
    _write_essential_csv(baci_csv / "cwi_essential_baci.csv", "cwi")
    _write_essential_csv(baci_csv / "cwe_essential_baci.csv", "cwe")
    _write_essential_csv(comtrade_csv / "cwi_essential_comtrade.csv", "cwi")
    _write_essential_csv(comtrade_csv / "cwe_essential_comtrade.csv", "cwe")
    return build_catalog(baci_csv=baci_csv, comtrade_csv=comtrade_csv, **kwargs)


def test_catalog_includes_essential_cwi_cwe_series(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    by_index = {(point["source_id"], point["index_id"]) for point in catalog["index_series"]}
    assert ("baci", "cwi_essential") in by_index
    assert ("baci", "cwe_essential") in by_index
    assert ("comtrade", "cwi_essential") in by_index
    assert ("comtrade", "cwe_essential") in by_index
    essential_table = next(
        table
        for table in catalog["tables"]
        if table["source_id"] == "baci"
        and table["data_type_id"] == "goods_trade"
        and table["product_group_id"] == "essential_commodities"
    )
    assert {row["index_id"] for row in essential_table["rows"]} >= {
        "import_index",
        "export_index",
        "cwi_essential",
        "cwe_essential",
    }


def test_catalog_matches_required_schema_keys(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    for key in SCHEMA_REQUIRED:
        assert key in catalog
    assert set(catalog["index_display"]) == set(GOODS_TRADE_INDEX_IDS)
    assert len(catalog["essential_divisions"]) == 20


def test_partners_are_three_and_partner_filter_is_off(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    assert [p["id"] for p in catalog["partners"]] == ["aus", "china", "us"]
    assert catalog["ui"]["partner_filter"] is False
    assert catalog["ui"]["index_toggles"] is False
    assert catalog["ui"]["goods_trade_index_ids"] == list(GOODS_TRADE_INDEX_IDS)


def test_catalog_has_required_keys_and_twenty_one_divisions(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    for key in (
        "generated_from",
        "sources",
        "data_types",
        "product_groups",
        "partners",
        "essential_divisions",
        "tables",
        "index_series",
    ):
        assert key in catalog
    assert len(catalog["essential_divisions"]) == 20
    goods = [
        t
        for t in catalog["tables"]
        if t["data_type_id"] == "goods_trade" and t["source_id"] == "baci"
    ]
    assert goods
    assert goods[0]["provenance"] == "study_output"
    services = [t for t in catalog["tables"] if t["data_type_id"] == "services"]
    assert services
    assert all(t["provenance"] == "mock" for t in services)


def test_services_are_mock_and_goods_are_study_output(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    services = [t for t in catalog["tables"] if t["data_type_id"] == "services"]
    goods = [t for t in catalog["tables"] if t["data_type_id"] == "goods_trade"]
    assert services
    assert all(t["provenance"] == "mock" for t in services)
    assert goods
    assert all(t["provenance"] == "study_output" for t in goods)


def test_filter_table_rows_pic_partner_year_and_essential():
    rows = [
        {"country": "Fiji", "year": 2013, "partner": "aus", "sitc2": "04"},
        {"country": "Fiji", "year": 2013, "partner": "china", "sitc2": "04"},
        {"country": "Samoa", "year": 2014, "partner": "aus", "sitc2": "67"},
        {"country": "Fiji", "year": 2013, "partner": "aus", "sitc2": "67"},
    ]
    filtered = filter_table_rows(
        rows,
        reporters=["Fiji"],
        partners=["aus"],
        year_min=2013,
        year_max=2013,
        product_group="essential_commodities",
        source_id="comtrade",
    )
    assert len(filtered) == 1
    assert filtered[0]["sitc2"] == "04"


def test_prefer_study_output_drops_mock_duplicates():
    points = [
        {
            "source_id": "baci",
            "country": "Fiji",
            "year": 2013,
            "partner": "aus",
            "index_id": "cwi",
            "value": 0.1,
            "provenance": "study_output",
        },
        {
            "source_id": "baci",
            "country": "Fiji",
            "year": 2013,
            "partner": "aus",
            "index_id": "cwi",
            "value": 0.9,
            "provenance": "mock",
        },
    ]
    kept = prefer_study_output(points)
    assert len(kept) == 1
    assert kept[0]["provenance"] == "study_output"
    assert {p["provenance"] for p in kept} == {"study_output"}


def test_write_catalog_roundtrip(tmp_path):
    baci_csv = tmp_path / "baci"
    comtrade_csv = tmp_path / "comtrade"
    _write_index_csv(baci_csv / "indices_baci.csv")
    out = tmp_path / "catalog.json"
    path = write_catalog(
        out,
        baci_csv=baci_csv,
        comtrade_csv=comtrade_csv,
        overlay_csv_dir=tmp_path / "empty",
        calendar_fallback=False,
    )
    assert path.exists()
    assert "Fiji" in path.read_text(encoding="utf-8")
    assert DEFAULT_CATALOG_PATH.as_posix().endswith("explorer-tool/public/data/catalog.json")


def test_overlay_missing_when_csvs_absent(tmp_path):
    overlay = load_overlay(csv_dir=tmp_path / "none", calendar_fallback=False)
    assert overlay["calendar_status"] == "missing"
    assert overlay["aid_status"] == "missing"
    assert overlay["disaster_status"] == "missing"
    assert overlay["calendar"] == []
    assert overlay["aid"] == []
    assert overlay["disasters"] == []


def test_overlay_copies_fixture_without_network(tmp_path):
    csv_dir = tmp_path / "overlay"
    csv_dir.mkdir()
    pd.DataFrame(
        [
            {
                "event_id": "covid_x",
                "year_start": 2020,
                "year_end": 2021,
                "country": "*",
                "partner": "*",
                "event_type": "covid",
                "title": "COVID",
            },
            {
                "event_id": "coup_x",
                "year_start": 2006,
                "year_end": 2006,
                "country": "Fiji",
                "partner": "aus",
                "event_type": "coup",
                "title": "Coup",
            },
        ]
    ).to_csv(csv_dir / "event_calendar.csv", index=False)
    pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2013,
                "partner": "aus",
                "lowy_spent_usd": 10.0,
            }
        ]
    ).to_csv(csv_dir / "lowy_aid_by_partner.csv", index=False)
    pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2016,
                "emdat_has_disaster": 1,
                "emdat_n_events": 2,
            }
        ]
    ).to_csv(csv_dir / "emdat_by_country_year.csv", index=False)
    overlay = load_overlay(csv_dir=csv_dir, calendar_fallback=False)
    assert overlay["calendar_status"] == "present"
    assert overlay["aid_status"] == "present"
    assert overlay["disaster_status"] == "present"
    by_id = {row["event_id"]: row for row in overlay["calendar"]}
    assert by_id["covid_x"]["encoding"] == "span"
    assert by_id["coup_x"]["encoding"] == "line"
    assert overlay["aid"][0]["lowy_spent_usd"] == 10.0
    assert overlay["disasters"][0]["emdat_has_disaster"] == 1


def test_mock_services_cover_partners_years_and_categories(tmp_path):
    catalog = _build_fixture_catalog(tmp_path, calendar_fallback=False, overlay_csv_dir=tmp_path / "empty")
    services = [table for table in catalog["tables"] if table["data_type_id"] == "services"]
    assert services
    groups = {table["product_group_id"] for table in services}
    assert groups == {"all_products", "essential_commodities"}
    sources = {table["source_id"] for table in services}
    assert sources == {"baci", "comtrade"}
    for table in services:
        assert table["provenance"] == "mock"
        assert "index_id" not in table["columns"]
        rows = table["rows"]
        assert rows
        assert {row["partner"] for row in rows} == {"aus", "china", "us"}
        years = {row["year"] for row in rows}
        assert years >= {2015, 2022}
        categories = {row["service_category"] for row in rows}
        if table["product_group_id"] == "all_products":
            assert categories == {"Travel", "Transport"}
        else:
            assert categories == {"Health", "Education"}


def test_analysis_packages_have_no_next_explorer_screens():
    for name in ANALYSIS_PACKAGES:
        package = SRC_DIR / name
        assert list(package.rglob("*.tsx")) == []
        for path in package.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "from next" not in text.lower()
            assert "next/app" not in text
