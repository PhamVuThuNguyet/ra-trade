"""Unit and integration tests for Comtrade / IMF STI and CWTI indices."""

import pandas as pd
import pytest

from trade_influence.imf_sti import compute_sti_imf
from trade_influence.indices import (
    compute_cwti,
    compute_indices,
    compute_sti,
    compute_sti_from_totals,
)
from trade_influence.prepare import build_hs2_panel, cmd_code_to_hs2
from trade_influence.visualize import (
    generate_all_plots,
    plot_index_timeseries_by_country,
)


def test_cmd_code_to_hs2_zero_pads_short_codes():
    assert cmd_code_to_hs2(111) == "01"
    assert cmd_code_to_hs2("112") == "01"
    assert cmd_code_to_hs2(1234) == "12"
    assert cmd_code_to_hs2("0201") == "02"


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


def test_build_hs2_panel_rolls_up_and_maps_partners():
    panel = build_hs2_panel(_toy_comtrade_raw())
    assert set(panel["partner"]) <= {"aus", "china", "world"}
    assert set(panel["hs2"]) == {"01", "02"}
    aus_imp_01 = panel[
        (panel["partner"] == "aus")
        & (panel["flow"] == "import")
        & (panel["hs2"] == "01")
    ].iloc[0]
    assert aus_imp_01["value_usd"] == pytest.approx(30.0)


def test_compute_sti_matches_hand_calculation():
    panel = build_hs2_panel(_toy_comtrade_raw())
    sti = compute_sti(panel)
    aus = sti[sti["partner"] == "aus"].iloc[0]
    assert aus["sti"] == pytest.approx(50.0 / 150.0)
    china = sti[sti["partner"] == "china"].iloc[0]
    assert china["sti"] == pytest.approx(5.0 / 150.0)


def test_compute_sti_imf_matches_hand_calculation():
    sti = compute_sti_imf(_toy_imf_raw())
    assert set(sti["partner"]) == {"aus", "china", "us"}
    assert sti[sti["partner"] == "aus"].iloc[0]["sti"] == pytest.approx(50.0 / 150.0)
    assert sti[sti["partner"] == "china"].iloc[0]["sti"] == pytest.approx(5.0 / 150.0)
    assert sti[sti["partner"] == "us"].iloc[0]["sti"] == pytest.approx(20.0 / 150.0)
    assert sti.iloc[0]["country"] == "Fiji"


def test_compute_sti_from_totals_shared_formula():
    totals = pd.DataFrame(
        [
            {"country": "Fiji", "year": 2013, "flow": "import", "partner": "aus", "total_usd": 40},
            {"country": "Fiji", "year": 2013, "flow": "export", "partner": "aus", "total_usd": 10},
            {"country": "Fiji", "year": 2013, "flow": "import", "partner": "world", "total_usd": 100},
            {"country": "Fiji", "year": 2013, "flow": "export", "partner": "world", "total_usd": 50},
        ]
    )
    sti = compute_sti_from_totals(totals, bilateral_partners=("aus",))
    assert sti.iloc[0]["sti"] == pytest.approx(50.0 / 150.0)


def test_compute_cwti_matches_hand_calculation():
    panel = build_hs2_panel(_toy_comtrade_raw())
    cwti = compute_cwti(panel)
    aus = cwti[cwti["partner"] == "aus"].iloc[0]
    assert aus["cwti"] == pytest.approx(0.24)
    china = cwti[cwti["partner"] == "china"].iloc[0]
    assert china["cwti"] == pytest.approx(0.005)


def test_compute_indices_merges_sti_and_cwti():
    panel = build_hs2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
    assert set(indices.columns) >= {"country", "year", "partner", "sti", "cwti"}
    assert len(indices) == 2


def test_sti_drops_zero_denominator_years():
    raw = pd.DataFrame(
        [
            _row("M", "AUS", 111, cif=10.0),
            _row("M", "W00", 111, cif=0.0),
            _row("X", "W00", 111, fob=0.0),
        ]
    )
    panel = build_hs2_panel(raw)
    sti = compute_sti(panel)
    assert sti.empty


def test_plot_index_timeseries_writes_file(tmp_path):
    panel = build_hs2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
    path = plot_index_timeseries_by_country(
        indices,
        "sti",
        ("aus", "china"),
        tmp_path,
        title="STI over time (Comtrade)",
        filename="timeseries_sti_comtrade.png",
    )
    assert path.exists()
    assert path.name == "timeseries_sti_comtrade.png"


def test_generate_all_plots_writes_timeseries_figures(tmp_path):
    panel = build_hs2_panel(_toy_comtrade_raw())
    indices = compute_indices(panel)
    sti_imf = compute_sti_imf(_toy_imf_raw())
    paths = generate_all_plots(indices, sti_imf, tmp_path)
    names = {p.name for p in paths}
    assert "timeseries_sti_comtrade.png" in names
    assert "timeseries_cwti_comtrade.png" in names
    assert "timeseries_sti_imf.png" in names
    assert "timeseries_sti_comtrade_vs_imf.png" in names
    assert "timeseries_sti_imf_by_partner_us.png" in names
    assert all(p.exists() for p in paths)


@pytest.mark.integration
def test_run_analysis_exports_csv_and_timeseries_plots(tmp_path):
    from trade_influence.pipeline import CORE_OUTPUT_FILES, run_analysis

    results = run_analysis(tmp_path)
    assert results["n_countries"] >= 1
    assert results["n_imf_countries"] >= 1
    assert results["n_imf_sti_observations"] >= 1
    assert set(results["comtrade_partners"]) == {"aus", "china"}
    assert set(results["imf_partners"]) == {"aus", "china", "us"}
    for name in CORE_OUTPUT_FILES:
        assert (tmp_path / "csv" / name).exists()
    assert (tmp_path / "plots" / "timeseries_sti_comtrade.png").exists()
    assert (tmp_path / "plots" / "timeseries_sti_imf.png").exists()
    assert (tmp_path / "plots" / "timeseries_sti_comtrade_vs_imf.png").exists()
    assert (tmp_path / "plots" / "timeseries_cwti_comtrade.png").exists()
    assert results["sti_comtrade"]["sti"].between(0, 1).all()
    assert results["sti_imf"]["sti"].between(0, 1).all()
    assert (results["cwti_comtrade"]["cwti"] >= 0).all()
    assert "us" in set(results["sti_imf"]["partner"])
