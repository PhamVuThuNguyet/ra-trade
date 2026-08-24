"""Unit tests for BACI HS02 characteristics tables and pipeline."""

import pandas as pd

import pytest

from baci.loaders import load_pic_flows, scan_baci
from baci.products import product_to_hs2, product_to_hs6
from baci_characteristics.pipeline import CORE_OUTPUT_FILES, run_analysis
from baci_characteristics.summarize import (
    availability_by_year,
    flow_by_year,
    overview,
    partner_gaps,
    prepare_pic_view,
    reporter_summary,
    reporter_year_panel,
    value_quantity_completeness,
)


def _country_codes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            (242, "Fiji", "FJ", "FJI"),
            (36, "Australia", "AU", "AUS"),
            (156, "China", "CN", "CHN"),
            (842, "USA", "US", "USA"),
            (296, "Kiribati", "KI", "KIR"),
            (90, "Solomon Isds", "SB", "SLB"),
            (520, "Nauru", "NR", "NRU"),
            (4, "Afghanistan", "AF", "AFG"),
            (12, "Algeria", "DZ", "DZA"),
        ],
        columns=["country_code", "country_name", "country_iso2", "country_iso3"],
    )


def _toy_flows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"t": 2003, "i": 242, "j": 36, "k": "080232", "v": 10.0, "q": 1.0},
            {"t": 2003, "i": 36, "j": 242, "k": "010110", "v": 20.0, "q": 2.0},
            {"t": 2003, "i": 242, "j": 156, "k": "080232", "v": 5.0, "q": None},
            {"t": 2003, "i": 4, "j": 12, "k": "010110", "v": 1.0, "q": 0.1},
            {"t": 2003, "i": 296, "j": 842, "k": "080232", "v": 3.0, "q": 0.5},
        ]
    )


def _write_baci_dir(tmp_path) -> tuple:
    baci_dir = tmp_path / "BACI_HS02_V202601"
    baci_dir.mkdir()
    _country_codes().to_csv(baci_dir / "country_codes_V202601.csv", index=False)
    pd.DataFrame(
        {"code": ["080232", "010110"], "description": ["nuts", "cattle"]}
    ).to_csv(baci_dir / "product_codes_HS02_V202601.csv", index=False)
    _toy_flows().to_csv(
        baci_dir / "BACI_HS02_Y2003_V202601.csv", index=False
    )
    cache_dir = tmp_path / "cache"
    return baci_dir, cache_dir


def test_product_to_hs2_pads_leading_zeros():
    assert product_to_hs6(80232) == "080232"
    assert product_to_hs2("080232") == "08"
    assert product_to_hs2("10110") == "01"
    assert product_to_hs2("010110") == "01"


def test_scan_baci_filters_to_pic_flows(tmp_path):
    baci_dir, _cache = _write_baci_dir(tmp_path)
    pic_flows, year_stats, shares = scan_baci(baci_dir, chunksize=10)
    assert len(pic_flows) == 4
    assert int(year_stats.iloc[0]["n_records"]) == 5
    assert int(year_stats.iloc[0]["n_pic_records"]) == 4
    assert int(year_stats.iloc[0]["year"]) == 2003
    aus_01 = shares[(shares["partner"] == "aus") & (shares["hs2"] == "01")].iloc[0]
    assert aus_01["export_share"] == pytest.approx(20.0 / 21.0)
    assert aus_01["import_share"] == pytest.approx(0.0)
    chn_08 = shares[(shares["partner"] == "china") & (shares["hs2"] == "08")].iloc[0]
    assert chn_08["import_share"] == pytest.approx(5.0 / 18.0)
    assert chn_08["export_share"] == pytest.approx(0.0)


def test_prepare_pic_view_splits_import_and_export():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    assert set(working["country"]) == {"Fiji", "Kiribati"}
    assert set(working["flow"]) == {"import", "export"}
    fiji_export = working[
        (working["country"] == "Fiji") & (working["flow"] == "export")
    ]
    assert len(fiji_export) == 2
    assert set(fiji_export["partner_iso3"]) == {"AUS", "CHN"}
    fiji_import = working[
        (working["country"] == "Fiji") & (working["flow"] == "import")
    ]
    assert len(fiji_import) == 1
    assert fiji_import.iloc[0]["partner_iso3"] == "AUS"


def test_availability_by_year_fills_requested_empty_years():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    availability = availability_by_year(working, years=(2002, 2003, 2004))
    assert list(availability["year"]) == [2002, 2003, 2004]
    assert list(availability["n_records"]) == [0, 4, 0]
    assert availability.loc[1, "n_reporters"] == 2


def test_reporter_year_panel_covers_requested_grid():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    panel = reporter_year_panel(
        working, reporters=("Fiji", "Kiribati", "Nauru"), years=(2003, 2004)
    )
    assert len(panel) == 6
    fiji_2003 = panel[(panel["country"] == "Fiji") & (panel["year"] == 2003)].iloc[0]
    nauru_2003 = panel[(panel["country"] == "Nauru") & (panel["year"] == 2003)].iloc[0]
    assert fiji_2003["present"] == 1
    assert nauru_2003["present"] == 0
    assert nauru_2003["iso3"] == "NRU"


def test_reporter_summary_includes_absent_requested_reporters():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    summary = reporter_summary(
        working, reporters=("Fiji", "Nauru"), years=(2003, 2004)
    )
    fiji = summary[summary["country"] == "Fiji"].iloc[0]
    nauru = summary[summary["country"] == "Nauru"].iloc[0]
    assert bool(fiji["observed"]) is True
    assert fiji["partners_focus"] == "AUS,CHN"
    assert bool(nauru["observed"]) is False
    assert nauru["n_records"] == 0


def test_partner_gaps_flags_missing_focus_partners():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    gaps = partner_gaps(working)
    kiribati = gaps[gaps["country"] == "Kiribati"].iloc[0]
    assert kiribati["flow"] == "export"
    assert "AUS" in kiribati["missing_partners"]
    assert "CHN" in kiribati["missing_partners"]
    fiji_import = gaps[
        (gaps["country"] == "Fiji") & (gaps["flow"] == "import")
    ].iloc[0]
    assert fiji_import["missing_partners"] == "CHN,USA"


def test_value_quantity_completeness_by_flow():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    completeness = value_quantity_completeness(working)
    exports = completeness[completeness["flow"] == "export"].iloc[0]
    assert exports["value_share"] == 1.0
    assert exports["qty_n"] == 2
    assert exports["n_records"] == 3


def test_overview_counts_full_dataset_and_pic_view():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    year_stats = pd.DataFrame(
        [{"year": 2003, "n_records": 5, "n_pic_records": 4}]
    )
    table = overview(
        working,
        year_stats,
        n_countries_meta=9,
        n_products_meta=2,
        reporters=("Fiji", "Kiribati", "Nauru"),
        years=(2003, 2004),
    )
    values = dict(zip(table["metric"], table["value"]))
    assert values["n_records_full"] == 5
    assert values["n_records_pic_view"] == 4
    assert values["n_reporters_observed"] == 2
    assert values["n_reporters_absent"] == 1
    assert values["n_reporter_years_requested"] == 6
    assert values["n_reporter_years_observed"] == 2


def test_flow_by_year_counts_import_and_export():
    working = prepare_pic_view(_toy_flows(), _country_codes())
    flows = flow_by_year(working)
    assert set(flows["flow"]) == {"import", "export"}
    assert int(flows.loc[flows["flow"] == "export", "n_records"].sum()) == 3


def test_pipeline_writes_csv_tables(tmp_path):
    baci_dir, cache_dir = _write_baci_dir(tmp_path)
    results = run_analysis(
        output_dir=tmp_path / "out",
        baci_dir=baci_dir,
        use_cache=True,
        cache_dir=cache_dir,
    )
    csv_dir = tmp_path / "out" / "csv"
    for filename in CORE_OUTPUT_FILES:
        assert (csv_dir / filename).exists()
    assert results["n_records_full"] == 5
    assert results["n_records_pic_view"] == 4
    assert results["n_reporters_observed"] == 2
    assert results["year_min"] == 2003
    assert (cache_dir / "pic_flows.csv").exists()
    assert (cache_dir / "global_hs2_shares.csv").exists()

    cached_flows, cached_stats = load_pic_flows(
        baci_dir, use_cache=True, cache_dir=cache_dir
    )
    assert len(cached_flows) == 4
    assert int(cached_stats.iloc[0]["n_records"]) == 5
