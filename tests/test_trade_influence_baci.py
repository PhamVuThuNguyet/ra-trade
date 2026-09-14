"""Unit tests for BACI HS-2 I, E, CWI, and CWE indices."""

import pandas as pd
import pytest

from baci.global_market import (
    chunk_hs2_totals,
    compute_global_market_shares,
)
from trade_influence.baci_pipeline import CORE_OUTPUT_FILES, run_baci_analysis
from trade_influence.baci_prepare import build_hs2_panel
from trade_influence.constants import COMMODITY_COL_HS2, INDEX_CWE, INDEX_CWI
from trade_influence.indices import (
    compute_cwe,
    compute_cwi,
    compute_import_export_indices,
    compute_indices,
)
from trade_influence.visualize import generate_baci_plots


def _row(year, exporter, importer, product, value, qty=1.0) -> dict:
    return {
        "t": year,
        "i": exporter,
        "j": importer,
        "k": product,
        "v": value,
        "q": qty,
    }


def _toy_baci_flows() -> pd.DataFrame:
    """Hand-checkable Fiji 2013 flows (values in thousand USD)."""
    return pd.DataFrame(
        [
            _row(2013, 36, 242, "080232", 30.0),
            _row(2013, 36, 242, "010110", 10.0),
            _row(2013, 156, 242, "080232", 5.0),
            _row(2013, 554, 242, "080232", 15.0),
            _row(2013, 554, 242, "010110", 40.0),
            _row(2013, 242, 36, "080232", 10.0),
            _row(2013, 242, 554, "080232", 40.0),
        ]
    )


def _write_baci_dir(tmp_path) -> tuple:
    baci_dir = tmp_path / "BACI_HS02_V202601"
    baci_dir.mkdir()
    pd.DataFrame(
        [
            (242, "Fiji", "FJ", "FJI"),
            (36, "Australia", "AU", "AUS"),
            (156, "China", "CN", "CHN"),
            (842, "USA", "US", "USA"),
            (554, "New Zealand", "NZ", "NZL"),
            (4, "Afghanistan", "AF", "AFG"),
            (12, "Algeria", "DZ", "DZA"),
        ],
        columns=["country_code", "country_name", "country_iso2", "country_iso3"],
    ).to_csv(baci_dir / "country_codes_V202601.csv", index=False)
    pd.DataFrame(
        {"code": ["080232", "010110"], "description": ["nuts", "cattle"]}
    ).to_csv(baci_dir / "product_codes_HS02_V202601.csv", index=False)
    _toy_baci_flows().to_csv(
        baci_dir / "BACI_HS02_Y2013_V202601.csv", index=False
    )
    return baci_dir, tmp_path / "cache"


def test_build_hs2_panel_maps_partners_and_builds_world():
    panel = build_hs2_panel(_toy_baci_flows())
    assert set(panel["partner"]) <= {"aus", "china", "us", "world"}
    assert set(panel[COMMODITY_COL_HS2]) == {"08", "01"}
    aus_imp_08 = panel[
        (panel["partner"] == "aus")
        & (panel["flow"] == "import")
        & (panel[COMMODITY_COL_HS2] == "08")
    ].iloc[0]
    assert aus_imp_08["value_usd"] == pytest.approx(30_000.0)
    world_imp = panel[
        (panel["partner"] == "world") & (panel["flow"] == "import")
    ]["value_usd"].sum()
    assert world_imp == pytest.approx(100_000.0)


def test_baci_import_export_indices_match_hand_calculation():
    panel = build_hs2_panel(_toy_baci_flows())
    shares = compute_import_export_indices(panel)
    aus = shares[shares["partner"] == "aus"].iloc[0]
    assert aus["import_index"] == pytest.approx(40.0 / 100.0)
    assert aus["export_index"] == pytest.approx(10.0 / 50.0)
    china = shares[shares["partner"] == "china"].iloc[0]
    assert china["import_index"] == pytest.approx(5.0 / 100.0)
    assert china["export_index"] == pytest.approx(0.0)
    us = shares[shares["partner"] == "us"].iloc[0]
    assert us["import_index"] == pytest.approx(0.0)
    assert us["export_index"] == pytest.approx(0.0)


def test_baci_cwi_cwe_match_hand_calculation():
    panel = build_hs2_panel(_toy_baci_flows())
    cwi = compute_cwi(panel, commodity_col=COMMODITY_COL_HS2)
    cwe = compute_cwe(panel, commodity_col=COMMODITY_COL_HS2)
    aus_cwi = cwi[cwi["partner"] == "aus"].iloc[0]
    aus_cwe = cwe[cwe["partner"] == "aus"].iloc[0]
    assert aus_cwi[INDEX_CWI] == pytest.approx(0.20)
    assert aus_cwe[INDEX_CWE] == pytest.approx(0.04)
    china_cwi = cwi[cwi["partner"] == "china"].iloc[0]
    china_cwe = cwe[cwe["partner"] == "china"].iloc[0]
    assert china_cwi[INDEX_CWI] == pytest.approx(0.005)
    assert china_cwe[INDEX_CWE] == pytest.approx(0.0)


def test_baci_global_market_shares_match_hand_calculation():
    world, exports, imports = chunk_hs2_totals(_toy_baci_flows())
    shares = compute_global_market_shares(world, exports, imports)
    aus_08 = shares[(shares["partner"] == "aus") & (shares["hs2"] == "08")].iloc[0]
    aus_01 = shares[(shares["partner"] == "aus") & (shares["hs2"] == "01")].iloc[0]
    assert aus_08["world_value"] == pytest.approx(100.0)
    assert aus_08["export_share"] == pytest.approx(30.0 / 100.0)
    assert aus_08["import_share"] == pytest.approx(10.0 / 100.0)
    assert aus_01["export_share"] == pytest.approx(10.0 / 50.0)
    assert aus_01["import_share"] == pytest.approx(0.0)
    china_08 = shares[(shares["partner"] == "china") & (shares["hs2"] == "08")].iloc[0]
    assert china_08["export_share"] == pytest.approx(5.0 / 100.0)
    assert china_08["import_share"] == pytest.approx(0.0)


def test_baci_cwi_cwe_apply_global_market_share():
    panel = build_hs2_panel(_toy_baci_flows())
    world, exports, imports = chunk_hs2_totals(_toy_baci_flows())
    shares = compute_global_market_shares(world, exports, imports)
    cwi = compute_cwi(
        panel, commodity_col=COMMODITY_COL_HS2, global_shares=shares
    )
    cwe = compute_cwe(
        panel, commodity_col=COMMODITY_COL_HS2, global_shares=shares
    )
    aus_cwi = cwi[cwi["partner"] == "aus"].iloc[0]
    aus_cwe = cwe[cwe["partner"] == "aus"].iloc[0]
    assert aus_cwi[INDEX_CWI] == pytest.approx(0.058)
    assert aus_cwe[INDEX_CWE] == pytest.approx(0.004)
    china_cwi = cwi[cwi["partner"] == "china"].iloc[0]
    assert china_cwi[INDEX_CWI] == pytest.approx(0.00025)


def test_baci_compute_indices_merges_all_four_measures():
    panel = build_hs2_panel(_toy_baci_flows())
    indices = compute_indices(panel, commodity_col=COMMODITY_COL_HS2)
    assert set(indices.columns) >= {
        "country",
        "year",
        "partner",
        "import_index",
        "export_index",
        INDEX_CWI,
        INDEX_CWE,
    }
    assert set(indices["partner"]) == {"aus", "china", "us"}


def test_generate_baci_plots_writes_timeseries_figures(tmp_path):
    panel = build_hs2_panel(_toy_baci_flows())
    indices = compute_indices(panel, commodity_col=COMMODITY_COL_HS2)
    paths = generate_baci_plots(indices, tmp_path)
    names = {path.name for path in paths}
    assert "timeseries_import_index_baci.png" in names
    assert "timeseries_export_index_baci.png" in names
    assert "timeseries_cwi_baci.png" in names
    assert "timeseries_cwe_baci.png" in names
    assert "timeseries_import_index_baci_by_partner_us.png" in names
    assert all(path.exists() for path in paths)


def test_run_baci_analysis_exports_csv_and_plots(tmp_path):
    baci_dir, cache_dir = _write_baci_dir(tmp_path)
    results = run_baci_analysis(
        output_dir=tmp_path / "out",
        baci_dir=baci_dir,
        use_cache=False,
        cache_dir=cache_dir,
    )
    assert results["n_countries"] == 1
    assert set(results["partners"]) == {"aus", "china", "us"}
    for name in CORE_OUTPUT_FILES:
        assert (tmp_path / "out" / "csv" / name).exists()
    assert (tmp_path / "out" / "csv" / "global_hs2_shares.csv").exists()
    assert (tmp_path / "out" / "plots" / "timeseries_import_index_baci.png").exists()
    assert (tmp_path / "out" / "plots" / "timeseries_cwi_baci.png").exists()
    indices = results["indices"]
    assert indices["import_index"].between(0, 1).all()
    assert indices["export_index"].between(0, 1).all()
    assert (indices[INDEX_CWI] >= 0).all()
    assert (indices[INDEX_CWE] >= 0).all()
    aus = indices[indices["partner"] == "aus"].iloc[0]
    assert aus[INDEX_CWI] == pytest.approx(0.058)
    assert aus[INDEX_CWE] == pytest.approx(0.004)
