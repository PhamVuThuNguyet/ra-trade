"""Unit and integration tests for Comtrade / IMF I, E, CWI, and CWE indices."""

import pandas as pd
import pytest

from trade_influence.constants import COMMODITY_COL, INDEX_CWE, INDEX_CWI
from trade_influence.imf_indices import compute_import_export_indices_imf
from trade_influence.indices import (
    compute_cwe,
    compute_cwi,
    compute_flow_share_from_totals,
    compute_import_export_indices,
    compute_indices,
)
from trade_influence.prepare import build_sitc2_panel, cmd_code_to_sitc2
from trade_influence.visualize import (
    generate_all_plots,
    plot_index_timeseries_by_country,
)


def test_cmd_code_to_sitc2_pads_stripped_ag3_codes():
    assert cmd_code_to_sitc2(1) == "00"
    assert cmd_code_to_sitc2(11) == "01"
    assert cmd_code_to_sitc2(111) == "11"
    assert cmd_code_to_sitc2("012") == "01"
    assert cmd_code_to_sitc2("211") == "21"


def _toy_comtrade_raw() -> pd.DataFrame:
    """Hand-checkable Comtrade-like rows for Fiji 2013."""
    rows = [
        _row("M", "AUS", 111, cif=30.0),
        _row("M", "W00", 111, cif=50.0),
        _row("M", "AUS", 211, cif=10.0),
        _row("M", "W00", 211, cif=50.0),
        _row("X", "AUS", 111, fob=10.0),
        _row("X", "W00", 111, fob=50.0),
        _row("M", "CHN", 111, cif=5.0),
        _row("M", "CHN", 211, cif=0.0),
    ]
    return pd.DataFrame(rows)


def _row(
    flow: str,
    partner: str,
    cmd: int,
    *,
    cif: float | None = None,
    fob: float | None = None,
) -> dict:
    value = cif if flow == "M" else fob
    return {
        "reporterDesc": "Fiji",
        "refYear": 2013,
        "flowCode": flow,
        "partnerISO": partner,
        "cmdCode": cmd,
        "cifvalue__US__": cif,
        "fobvalue__US__": fob,
        "primaryValue__US__": value,
    }


def _toy_imf_raw() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "country": "Fiji, Republic of",
                "time_period": 2013,
                "exports_world": 50.0,
                "imports_world": 100.0,
                "exports_aus": 10.0,
                "imports_aus": 40.0,
                "exports_china": 0.0,
                "imports_china": 5.0,
                "exports_us": 8.0,
                "imports_us": 12.0,
            }
        ]
    )


def test_build_sitc2_panel_rolls_up_and_maps_partners():
    panel = build_sitc2_panel(_toy_comtrade_raw())
    assert set(panel["partner"]) <= {"aus", "china", "us", "world"}
    assert set(panel[COMMODITY_COL]) == {"11", "21"}
    aus_imp_11 = panel[
        (panel["partner"] == "aus")
        & (panel["flow"] == "import")
        & (panel[COMMODITY_COL] == "11")
    ].iloc[0]
    assert aus_imp_11["value_usd"] == pytest.approx(30.0)


def test_compute_import_export_indices_match_hand_calculation():
    panel = build_sitc2_panel(_toy_comtrade_raw())
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


def test_compute_import_export_indices_imf_match_hand_calculation():
    indices = compute_import_export_indices_imf(_toy_imf_raw())
    assert set(indices["partner"]) == {"aus", "china", "us"}
    aus = indices[indices["partner"] == "aus"].iloc[0]
    assert aus["import_index"] == pytest.approx(40.0 / 100.0)
    assert aus["export_index"] == pytest.approx(10.0 / 50.0)
    china = indices[indices["partner"] == "china"].iloc[0]
    assert china["import_index"] == pytest.approx(5.0 / 100.0)
    assert china["export_index"] == pytest.approx(0.0)
    us = indices[indices["partner"] == "us"].iloc[0]
    assert us["import_index"] == pytest.approx(12.0 / 100.0)
    assert us["export_index"] == pytest.approx(8.0 / 50.0)
    assert indices.iloc[0]["country"] == "Fiji"


def test_compute_flow_share_from_totals():
    totals = pd.DataFrame(
        [
            {"country": "Fiji", "year": 2013, "flow": "import", "partner": "aus", "total_usd": 40},
            {"country": "Fiji", "year": 2013, "flow": "export", "partner": "aus", "total_usd": 10},
            {"country": "Fiji", "year": 2013, "flow": "import", "partner": "world", "total_usd": 100},
            {"country": "Fiji", "year": 2013, "flow": "export", "partner": "world", "total_usd": 50},
        ]
    )
    shares = compute_flow_share_from_totals(totals, bilateral_partners=("aus",))
    import_share = shares[shares["flow"] == "import"].iloc[0]["share"]
    export_share = shares[shares["flow"] == "export"].iloc[0]["share"]
    assert import_share == pytest.approx(40.0 / 100.0)
    assert export_share == pytest.approx(10.0 / 50.0)


def test_compute_cwi_cwe_match_hand_calculation():
    panel = build_sitc2_panel(_toy_comtrade_raw())
    cwi = compute_cwi(panel)
    cwe = compute_cwe(panel)
    aus_cwi = cwi[cwi["partner"] == "aus"].iloc[0]
    aus_cwe = cwe[cwe["partner"] == "aus"].iloc[0]
    assert aus_cwi[INDEX_CWI] == pytest.approx(0.20)
    assert aus_cwe[INDEX_CWE] == pytest.approx(0.04)
    china_cwi = cwi[cwi["partner"] == "china"].iloc[0]
    china_cwe = cwe[cwe["partner"] == "china"].iloc[0]
    assert china_cwi[INDEX_CWI] == pytest.approx(0.005)
    assert china_cwe[INDEX_CWE] == pytest.approx(0.0)


def test_compute_indices_merges_all_four_measures():
    panel = build_sitc2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
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


def test_import_index_drops_zero_denominator_years():
    raw = pd.DataFrame(
        [
            _row("M", "AUS", 111, cif=10.0),
            _row("M", "W00", 111, cif=0.0),
            _row("X", "W00", 111, fob=0.0),
        ]
    )
    panel = build_sitc2_panel(raw)
    shares = compute_import_export_indices(panel)
    assert shares.empty


def test_plot_index_timeseries_writes_file(tmp_path):
    panel = build_sitc2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
    path = plot_index_timeseries_by_country(
        indices,
        "import_index",
        ("aus", "china", "us"),
        tmp_path,
        title="Import index I over time (Comtrade)",
        filename="timeseries_import_index_comtrade.png",
    )
    assert path.exists()
    assert path.name == "timeseries_import_index_comtrade.png"


def test_generate_all_plots_writes_timeseries_figures(tmp_path):
    panel = build_sitc2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
    indices_imf = compute_import_export_indices_imf(_toy_imf_raw())
    paths = generate_all_plots(indices, indices_imf, tmp_path)
    names = {p.name for p in paths}
    assert "timeseries_import_index_comtrade.png" in names
    assert "timeseries_export_index_comtrade.png" in names
    assert "timeseries_cwi_comtrade.png" in names
    assert "timeseries_cwe_comtrade.png" in names
    assert "timeseries_import_index_imf.png" in names
    assert "timeseries_import_index_comtrade_vs_imf.png" in names
    assert "timeseries_import_index_comtrade_by_partner_us.png" in names
    assert "timeseries_import_index_comtrade_vs_imf_by_partner_aus.png" in names
    assert all(p.exists() for p in paths)


@pytest.mark.integration
def test_run_analysis_exports_csv_and_timeseries_plots(tmp_path):
    from trade_influence.pipeline import CORE_OUTPUT_FILES, run_analysis

    results = run_analysis(tmp_path)
    assert results["n_countries"] >= 1
    assert results["n_imf_countries"] >= 1
    assert results["n_imf_observations"] >= 1
    assert set(results["partners"]) == {"aus", "china", "us"}
    for name in CORE_OUTPUT_FILES:
        assert (tmp_path / "csv" / name).exists()
    assert (tmp_path / "plots" / "timeseries_import_index_comtrade.png").exists()
    assert (tmp_path / "plots" / "timeseries_cwi_comtrade.png").exists()
    assert (tmp_path / "plots" / "timeseries_cwe_comtrade.png").exists()
    assert (tmp_path / "plots" / "timeseries_import_index_imf.png").exists()
    assert (tmp_path / "plots" / "timeseries_import_index_comtrade_vs_imf.png").exists()
    assert (tmp_path / "plots" / "timeseries_import_index_comtrade_by_partner_us.png").exists()
    comtrade = results["indices_comtrade"]
    imf = results["indices_imf"]
    assert comtrade["import_index"].between(0, 1).all()
    assert comtrade["export_index"].between(0, 1).all()
    assert imf["import_index"].between(0, 1).all()
    assert imf["export_index"].between(0, 1).all()
    assert (comtrade[INDEX_CWI] >= 0).all()
    assert (comtrade[INDEX_CWE] >= 0).all()
    assert "us" in set(comtrade["partner"])
    assert "us" in set(imf["partner"])
