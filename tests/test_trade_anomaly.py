"""Unit and integration tests for multi-scale trade anomaly detection."""

import numpy as np
import pandas as pd
import pytest

from trade_anomaly.acf_diagnostics import sample_acf, suggest_min_window
from trade_anomaly.constants import (
    TIER_ALERT,
    TIER_CRITICAL,
    TIER_WATCH,
    TYPE_LEVEL_SHOCK,
    TYPE_STRUCTURAL_BREAK,
)
from trade_anomaly.detect import robust_scale, score_series
from trade_anomaly.fuse import classify_tier, classify_type, fuse_scores
from trade_anomaly.models import forecast_ar1, forecast_holt, forecast_naive
from trade_anomaly.prepare import build_series_panel, compute_flow_sti
from trade_anomaly.windows import iter_window_forecast_points
from trade_influence.prepare import build_sitc2_panel


def _row(
    flow: str,
    partner: str,
    cmd: int,
    year: int,
    *,
    cif: float | None = None,
    fob: float | None = None,
    reporter: str = "Fiji",
) -> dict:
    value = cif if flow == "M" else fob
    return {
        "reporterDesc": reporter,
        "refYear": year,
        "flowCode": flow,
        "partnerISO": partner,
        "cmdCode": cmd,
        "cifvalue__US__": cif,
        "fobvalue__US__": fob,
        "primaryValue__US__": value,
    }


def _toy_multi_year_raw() -> pd.DataFrame:
    """Stable series with a 2016 import spike vs Australia."""
    rows = []
    for year in range(2010, 2018):
        aus_imp = 100.0 if year != 2016 else 400.0
        rows.extend(
            [
                _row("M", "AUS", 111, year, cif=aus_imp),
                _row("M", "W00", 111, year, cif=aus_imp + 50.0),
                _row("X", "AUS", 111, year, fob=20.0),
                _row("X", "W00", 111, year, fob=50.0),
                _row("M", "USA", 111, year, cif=10.0),
                _row("X", "USA", 111, year, fob=5.0),
                _row("M", "CHN", 111, year, cif=15.0),
                _row("X", "CHN", 111, year, fob=8.0),
            ]
        )
    return pd.DataFrame(rows)


def test_forecast_naive_returns_last_value():
    assert forecast_naive(np.array([1.0, 2.0, 3.0])) == pytest.approx(3.0)


def test_forecast_holt_follows_linear_trend():
    history = np.arange(1.0, 8.0)
    pred = forecast_holt(history)
    assert pred == pytest.approx(8.0, abs=1.5)


def test_forecast_ar1_recovers_mean_reverting_process():
    rng = np.random.default_rng(0)
    y = np.zeros(30)
    for t in range(1, 30):
        y[t] = 0.5 * y[t - 1] + rng.normal(0, 0.1)
    pred = forecast_ar1(y[:-1])
    assert np.isfinite(pred)


def test_robust_scale_handles_constant_series():
    assert robust_scale(np.array([0.0, 0.0, 0.0])) == pytest.approx(1.0)


def test_iter_window_forecast_points_stride():
    series = pd.DataFrame({"year": [2010, 2011, 2012, 2013], "value": [1, 2, 3, 4]})
    points = list(iter_window_forecast_points(series, window=2, stride=1))
    assert [p[0] for p in points] == [2012, 2013]
    assert list(points[0][1]) == pytest.approx([1, 2])


def test_sample_acf_lag1_high_for_persistent_series():
    values = np.linspace(0, 1, 20)
    acf = sample_acf(values, max_lag=3)
    assert acf.loc[acf["lag"] == 1, "acf"].iloc[0] > 0.5
    assert suggest_min_window(acf, bound=0.3) >= 1


def test_classify_tier_ultra_short_alone_is_watch_not_critical():
    assert classify_tier({1: 5.0}) == TIER_WATCH
    assert classify_tier({1: 5.0}) != TIER_CRITICAL


def test_classify_tier_structural_consensus_is_critical():
    assert classify_tier({3: 3.2, 5: 3.1, 1: 0.5}) == TIER_CRITICAL


def test_classify_tier_alert_needs_structural_support():
    assert classify_tier({1: 2.6, 3: 2.6}) == TIER_ALERT
    assert classify_tier({3: 2.6, 5: 2.7}) == TIER_ALERT


def test_classify_type_level_shock_vs_break():
    assert classify_type({1: 3.0}, TIER_WATCH) == TYPE_LEVEL_SHOCK
    assert (
        classify_type({5: 3.0, 7: 2.5}, TIER_ALERT) == TYPE_STRUCTURAL_BREAK
    )


def test_score_series_flags_spike():
    years = list(range(2010, 2018))
    values = [100.0] * len(years)
    values[years.index(2016)] = 400.0
    series = pd.DataFrame(
        {
            "series_id": ["demo"] * len(years),
            "country": ["Fiji"] * len(years),
            "partner": ["aus"] * len(years),
            "flow": ["import"] * len(years),
            "metric": ["raw_usd"] * len(years),
            "year": years,
            "value": values,
        }
    )
    scores = score_series(series, windows=(1, 3, 5))
    spike = scores[(scores["year"] == 2016) & (scores["window"] == 1)]
    assert not spike.empty
    assert spike["abs_z"].max() > 1.0


def test_fuse_scores_emits_tiers():
    scores = pd.DataFrame(
        [
            {
                "series_id": "s1",
                "country": "Fiji",
                "partner": "aus",
                "flow": "import",
                "metric": "raw_usd",
                "year": 2016,
                "window": 1,
                "model": "naive",
                "abs_z": 4.0,
                "z": 4.0,
            },
            {
                "series_id": "s1",
                "country": "Fiji",
                "partner": "aus",
                "flow": "import",
                "metric": "raw_usd",
                "year": 2016,
                "window": 3,
                "model": "holt",
                "abs_z": 2.7,
                "z": 2.7,
            },
        ]
    )
    alerts = fuse_scores(scores)
    assert len(alerts) == 1
    assert alerts.iloc[0]["tier"] == TIER_ALERT


def test_build_sitc2_panel_accepts_usa():
    raw = _toy_multi_year_raw()
    panel = build_sitc2_panel(
        raw, bilateral_partner_isos=("AUS", "CHN", "USA")
    )
    assert "us" in set(panel["partner"])


def test_build_series_panel_includes_raw_sti_cwti_and_us():
    panel = build_sitc2_panel(
        _toy_multi_year_raw(),
        bilateral_partner_isos=("AUS", "CHN", "USA"),
    )
    series = build_series_panel(panel)
    assert {"raw_usd", "sti", "cwti"} <= set(series["metric"])
    assert "us" in set(series["partner"])
    assert {"import", "export", "total"} <= set(series["flow"])


def test_compute_flow_sti_hand_check():
    totals = pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "import",
                "partner": "aus",
                "total_usd": 40,
            },
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "import",
                "partner": "world",
                "total_usd": 100,
            },
        ]
    )
    sti = compute_flow_sti(totals, bilateral_partners=("aus",))
    assert sti.iloc[0]["sti"] == pytest.approx(0.4)


def test_worked_example_plot_writes_file(tmp_path):
    from trade_anomaly.worked_examples import plot_worked_example

    series = pd.DataFrame(
        {
            "series_id": ["Samoa|china|export|raw_usd"] * 5,
            "country": ["Samoa"] * 5,
            "partner": ["china"] * 5,
            "flow": ["export"] * 5,
            "metric": ["raw_usd"] * 5,
            "year": [2012, 2013, 2014, 2015, 2016],
            "value": [170.0, 137277.0, 7675.0, 825073.0, 798996.0],
        }
    )
    alerts = pd.DataFrame(
        [
            {
                "series_id": "Samoa|china|export|raw_usd",
                "country": "Samoa",
                "partner": "china",
                "flow": "export",
                "metric": "raw_usd",
                "year": 2015,
                "tier": "critical",
                "anomaly_type": "structural_break",
                "z_w1": 6.0,
                "z_w3": 12.0,
                "z_w5": 11.0,
                "z_w7": np.nan,
            },
            {
                "series_id": "Samoa|china|export|raw_usd",
                "country": "Samoa",
                "partner": "china",
                "flow": "export",
                "metric": "raw_usd",
                "year": 2016,
                "tier": "critical",
                "anomaly_type": "structural_break",
                "z_w1": 0.2,
                "z_w3": 6.5,
                "z_w5": 7.0,
                "z_w7": 15.0,
            },
        ]
    )
    example = {
        "series_id": "Samoa|china|export|raw_usd",
        "focus_years": (2015, 2016),
        "filename": "example_samoa_china_export_raw.png",
        "title": "Test Samoa–China",
        "ylabel": "Export value (USD)",
        "value_scale": 1.0,
    }
    path = plot_worked_example(series, alerts, example, tmp_path)
    assert path is not None
    assert path.exists()


@pytest.mark.integration
def test_run_analysis_exports_core_outputs(tmp_path):
    from trade_anomaly.pipeline import CORE_OUTPUT_FILES, run_analysis

    results = run_analysis(tmp_path)
    assert results["n_countries"] >= 1
    assert results["n_series"] >= 1
    assert set(results["partners"]) == {"aus", "china", "us"}
    assert results["windows"] == [1, 3, 5, 7]
    for name in CORE_OUTPUT_FILES:
        assert (tmp_path / "csv" / name).exists()
    assert (tmp_path / "plots" / "tier_counts.png").exists()
    assert (tmp_path / "plots" / "multiscale_z_heatmap.png").exists()
    assert (tmp_path / "plots" / "example_samoa_china_export_raw.png").exists()
    assert (tmp_path / "plots" / "example_fiji_china_total_sti.png").exists()
    assert (tmp_path / "plots" / "example_tonga_aus_export_raw.png").exists()
    assert (tmp_path / "plots" / "example_fiji_aus_export_cwti.png").exists()
    assert (tmp_path / "plots" / "example_worked_findings_overview.png").exists()
    assert results["alerts"]["tier"].isin(
        ["none", "watch", "alert", "critical"]
    ).all()
