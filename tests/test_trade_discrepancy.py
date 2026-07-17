import pandas as pd
import pytest

from trade_discrepancy.constants import COMTRADE_TO_IMF_COUNTRY, USD_TO_MILLIONS
from trade_discrepancy.harmonize import aggregate_comtrade, melt_imf, merge_sources, trade_value_usd
from trade_discrepancy.loaders import build_comparison_table
from trade_discrepancy.metrics import add_discrepancy_metrics, coverage_summary
from trade_discrepancy.visualize import (
    plot_layered_value_timeseries,
    plot_layered_value_timeseries_by_partner,
)


def _sample_comtrade_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reporterDesc": "Fiji",
                "refYear": 2013,
                "flowCode": "M",
                "partnerISO": "AUS",
                "cifvalue__US__": 100.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 100.0,
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2013,
                "flowCode": "M",
                "partnerISO": "W00",
                "cifvalue__US__": 200.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 200.0,
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2013,
                "flowCode": "X",
                "partnerISO": "W00",
                "cifvalue__US__": None,
                "fobvalue__US__": 300.0,
                "primaryValue__US__": 300.0,
            },
        ]
    )


def test_trade_value_usd_uses_cif_for_imports_and_fob_for_exports():
    row_import = _sample_comtrade_rows().iloc[0]
    row_export = _sample_comtrade_rows().iloc[2]
    assert trade_value_usd(row_import) == 100.0
    assert trade_value_usd(row_export) == 300.0


def test_aggregate_comtrade_converts_to_millions_and_maps_partners():
    aggregated = aggregate_comtrade(_sample_comtrade_rows())
    aus_import = aggregated[
        (aggregated["partner"] == "aus")
        & (aggregated["flow"] == "import")
        & (aggregated["year"] == 2013)
    ].iloc[0]
    world_export = aggregated[
        (aggregated["partner"] == "world")
        & (aggregated["flow"] == "export")
    ].iloc[0]
    assert aus_import["comtrade_value_musd"] == 100.0 / USD_TO_MILLIONS
    assert world_export["comtrade_value_musd"] == 300.0 / USD_TO_MILLIONS


def test_melt_imf_produces_long_format():
    imf = pd.DataFrame(
        [
            {
                "country": "Fiji, Republic of",
                "time_period": 2013,
                "exports_world": 10.0,
                "imports_world": 20.0,
                "exports_aus": 1.0,
                "imports_aus": 2.0,
                "exports_china": 3.0,
                "imports_china": 4.0,
                "exports_us": 5.0,
                "imports_us": 6.0,
            }
        ]
    )
    long = melt_imf(imf)
    assert set(long["partner"]) == {"world", "aus", "china", "us"}
    assert len(long) == 8


def test_merge_sources_aligns_country_names():
    comtrade_long = pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "import",
                "partner": "world",
                "comtrade_value_musd": 2.0,
            }
        ]
    )
    imf_long = pd.DataFrame(
        [
            {
                "country": "Fiji, Republic of",
                "year": 2013,
                "flow": "import",
                "partner": "world",
                "imf_value_musd": 2.1,
            }
        ]
    )
    merged = merge_sources(comtrade_long, imf_long, COMTRADE_TO_IMF_COUNTRY)
    assert len(merged) == 1
    assert merged.iloc[0]["country"] == "Fiji, Republic of"


def test_add_discrepancy_metrics_symmetric_pct():
    comparison = pd.DataFrame(
        [{"imf_value_musd": 110.0, "comtrade_value_musd": 100.0}]
    )
    metrics = add_discrepancy_metrics(comparison)
    assert metrics.iloc[0]["abs_diff_musd"] == pytest.approx(10.0)
    assert metrics.iloc[0]["symmetric_pct_diff"] == pytest.approx(
        200 * 10 / (110 + 100)
    )


def _sample_metrics() -> pd.DataFrame:
    rows = []
    for year in (2013, 2014):
        rows.append(
            {
                "country": "Fiji, Republic of",
                "country_comtrade": "Fiji",
                "year": year,
                "flow": "import",
                "partner": "world",
                "comtrade_value_musd": 100.0 + year - 2013,
                "imf_value_musd": 105.0 + year - 2013,
            }
        )
        rows.append(
            {
                "country": "Fiji, Republic of",
                "country_comtrade": "Fiji",
                "year": year,
                "flow": "export",
                "partner": "aus",
                "comtrade_value_musd": 50.0,
                "imf_value_musd": 52.0,
            }
        )
    return add_discrepancy_metrics(pd.DataFrame(rows))


def test_plot_layered_value_timeseries_writes_country_figures(tmp_path):
    metrics = _sample_metrics()
    paths = plot_layered_value_timeseries(metrics, tmp_path)
    assert len(paths) == 1
    assert paths[0].name == "layered_values_fiji.png"
    assert paths[0].exists()


def test_plot_labels_map_imf_country_names_to_comtrade(tmp_path):
    metrics = add_discrepancy_metrics(
        pd.DataFrame(
            [
                {
                    "country": "Palau, Republic of",
                    "year": 2016,
                    "flow": "import",
                    "partner": "world",
                    "comtrade_value_musd": 10.0,
                    "imf_value_musd": 12.0,
                }
            ]
        )
    )
    paths = plot_layered_value_timeseries(metrics, tmp_path)
    assert paths[0].name == "layered_values_palau.png"


def test_plot_layered_value_timeseries_by_partner_writes_overview(tmp_path):
    metrics = _sample_metrics()
    paths = plot_layered_value_timeseries_by_partner(metrics, tmp_path)
    assert {path.name for path in paths} == {"layered_values_overview_world.png", "layered_values_overview_aus.png"}
    assert all(path.exists() for path in paths)


def test_partner_headline_metrics_and_largest_gaps():
    from trade_discrepancy.pipeline import (
        largest_world_discrepancies,
        partner_headline_metrics,
    )

    metrics = _sample_metrics()
    by_partner = partner_headline_metrics(metrics)
    assert set(by_partner["partner"]) == {"world", "aus"}
    assert by_partner["n_observations"].sum() == len(metrics)

    top = largest_world_discrepancies(metrics, n=5)
    assert len(top) == 2  # sample has two world rows
    assert "symmetric_pct_diff" in top.columns
    assert top["symmetric_pct_diff"].abs().is_monotonic_decreasing or len(top) <= 1


@pytest.mark.integration
def test_run_analysis_covers_all_dimensions_and_exports(tmp_path):
    from trade_discrepancy.pipeline import ANALYSIS_DIMENSIONS, run_analysis

    results = run_analysis(tmp_path)
    assert results["analysis_dimensions"] == list(ANALYSIS_DIMENSIONS)
    assert results["n_comparable_observations"] == 244
    assert results["n_world_observations"] == 86
    assert "extended" not in results
    assert (tmp_path / "csv" / "comparison_metrics.csv").exists()
    assert (tmp_path / "csv" / "summary_by_partner.csv").exists()
    assert (tmp_path / "csv" / "largest_world_discrepancies.csv").exists()
    assert not (tmp_path / "csv" / "valuation_headline.csv").exists()
    assert not (tmp_path / "csv" / "consistency_patterns.csv").exists()
    assert not (tmp_path / "plots" / "valuation_sensitivity.png").exists()
    assert (tmp_path / "plots" / "scatter_world_totals.png").exists()
    assert results["csv_dir"].endswith("csv")
    assert results["plots_dir"].endswith("plots")


@pytest.mark.integration
def test_build_comparison_table_has_world_totals_for_fiji_2013():
    comparison, _, _ = build_comparison_table()
    fiji_world_import_2013 = comparison[
        (comparison["country"] == "Fiji, Republic of")
        & (comparison["year"] == 2013)
        & (comparison["flow"] == "import")
        & (comparison["partner"] == "world")
    ]
    assert len(fiji_world_import_2013) == 1
    row = fiji_world_import_2013.iloc[0]
    assert row["comtrade_value_musd"] == pytest.approx(2825.73, rel=0.01)
    assert row["imf_value_musd"] == pytest.approx(2910.79, rel=0.01)


@pytest.mark.integration
def test_aus_bilateral_matches_closely_for_fiji_2013():
    comparison, _, _ = build_comparison_table()
    row = comparison[
        (comparison["country"] == "Fiji, Republic of")
        & (comparison["year"] == 2013)
        & (comparison["flow"] == "import")
        & (comparison["partner"] == "aus")
    ].iloc[0]
    metrics = add_discrepancy_metrics(pd.DataFrame([row]))
    assert metrics.iloc[0]["symmetric_pct_diff"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.integration
def test_coverage_summary_lists_all_overlap_countries():
    _, comtrade_long, imf_long = build_comparison_table()
    coverage = coverage_summary(comtrade_long, imf_long)
    assert len(coverage) == len(COMTRADE_TO_IMF_COUNTRY)
    assert coverage["overlap_years"].min() >= 1
