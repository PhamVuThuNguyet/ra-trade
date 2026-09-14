import pandas as pd
import pytest

from trade_discrepancy.constants import (
    COMTRADE_FILENAME,
    COMTRADE_TO_IMF_COUNTRY,
    USD_TO_MILLIONS,
)
from trade_discrepancy.harmonize import (
    aggregate_comtrade,
    melt_imf,
    merge_sources,
    trade_value_series,
    trade_value_usd,
)
from trade_discrepancy.loaders import build_comparison_table
from trade_discrepancy.metrics import add_discrepancy_metrics
from trade_discrepancy.visualize import (
    generate_all_plots,
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
    rows = _sample_comtrade_rows()
    assert trade_value_usd(rows.iloc[0]) == 100.0
    assert trade_value_usd(rows.iloc[2]) == 300.0
    series = trade_value_series(rows)
    assert list(series) == [100.0, 200.0, 300.0]


def test_aggregate_comtrade_converts_to_millions_and_maps_partners():
    aggregated = aggregate_comtrade(_sample_comtrade_rows())
    aus_import = aggregated[
        (aggregated["partner"] == "aus")
        & (aggregated["flow"] == "import")
        & (aggregated["year"] == 2013)
    ].iloc[0]
    world_export = aggregated[
        (aggregated["partner"] == "world") & (aggregated["flow"] == "export")
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
    paths = plot_layered_value_timeseries_by_partner(metrics, tmp_path)
    assert paths[0].name == "layered_values_overview_world.png"


def test_plot_layered_value_timeseries_by_partner_writes_overview(tmp_path):
    metrics = _sample_metrics()
    paths = plot_layered_value_timeseries_by_partner(metrics, tmp_path)
    assert {path.name for path in paths} == {
        "layered_values_overview_world.png",
        "layered_values_overview_aus.png",
    }
    assert all(path.exists() for path in paths)


def test_generate_all_plots_keeps_needed_charts_and_removes_stale(tmp_path):
    from trade_discrepancy.metrics import summarize_discrepancies

    stale = tmp_path / "coverage_overlap_years.png"
    stale.write_bytes(b"stale")
    metrics = _sample_metrics()
    paths = generate_all_plots(metrics, summarize_discrepancies(metrics), tmp_path)
    names = {path.name for path in paths}
    assert "scatter_world_totals.png" in names
    assert "heatmap_median_discrepancy.png" in names
    assert "layered_values_overview_world.png" in names
    assert "timeseries_world.png" in names
    assert not stale.exists()
    assert "coverage_overlap_years.png" not in names
    assert "layered_values_fiji.png" not in names


def test_partner_headline_metrics_and_largest_gaps():
    from trade_discrepancy.metrics import (
        largest_world_discrepancies,
        partner_headline_metrics,
    )

    metrics = _sample_metrics()
    by_partner = partner_headline_metrics(metrics)
    assert list(by_partner["partner"]) == ["world", "aus"]
    assert by_partner["n_observations"].sum() == len(metrics)

    top = largest_world_discrepancies(metrics, n=5)
    assert len(top) == 2
    assert "symmetric_pct_diff" in top.columns


def test_resolve_comtrade_paths_defaults_to_latest_extract():
    from trade_discrepancy.constants import COMTRADE_DIR
    from trade_discrepancy.loaders import resolve_comtrade_paths

    paths = resolve_comtrade_paths()
    assert len(paths) == 1
    assert paths[0] == COMTRADE_DIR / COMTRADE_FILENAME


def test_normalize_comtrade_schema_maps_unsuffixed_value_columns():
    from trade_discrepancy.loaders import normalize_comtrade_schema

    raw = pd.DataFrame(
        [
            {
                "reporterDesc": "Fiji",
                "refYear": "2008",
                "flowCode": "M",
                "partnerISO": "AUS",
                "cifvalue": "100",
                "fobvalue": "",
                "primaryValue": "100",
            }
        ]
    )
    normalized = normalize_comtrade_schema(raw)
    assert "cifvalue__US__" in normalized.columns
    assert normalized.iloc[0]["cifvalue__US__"] == 100.0


def test_comtrade_extract_label_from_filename():
    from trade_discrepancy.loaders import comtrade_extract_label

    assert (
        comtrade_extract_label("TradeData_sitc4_ag3_2000_2024.csv")
        == "sitc4_ag3_2000_2024"
    )
    assert comtrade_extract_label("TradeData_2008_2012.csv") == "2008_2012"


def test_comtrade_availability_by_year_counts_records_and_countries():
    from trade_discrepancy.loaders import comtrade_availability_by_year

    raw = pd.DataFrame(
        [
            {"reporterDesc": "Fiji", "refYear": 2008},
            {"reporterDesc": "Fiji", "refYear": 2008},
            {"reporterDesc": "Cook Isds", "refYear": 2008},
            {"reporterDesc": "Solomon Isds", "refYear": 2009},
        ]
    )
    availability = comtrade_availability_by_year(raw)
    assert list(availability["year"]) == [2008, 2009]
    assert availability.loc[0, "n_records"] == 3
    assert availability.loc[0, "n_countries"] == 2
    assert availability.loc[0, "countries"] == "Cook Islands, Fiji"
    assert availability.loc[1, "n_records"] == 1
    assert availability.loc[1, "countries"] == "Solomon Islands"


def _sample_metadata_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    comtrade_raw = pd.DataFrame(
        [
            {
                "reporterDesc": "Fiji",
                "refYear": 2008,
                "partnerISO": "USA",
                "cmdCode": "001",
                "classificationCode": "S4",
                "freqCode": "A",
                "flowCode": "M",
                "cifvalue__US__": 10.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 10.0,
                "comtrade_extract": "sitc4_ag3_2000_2024",
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2013,
                "partnerISO": "W00",
                "cmdCode": "011",
                "classificationCode": "S4",
                "freqCode": "A",
                "flowCode": "X",
                "cifvalue__US__": None,
                "fobvalue__US__": 20.0,
                "primaryValue__US__": 20.0,
                "comtrade_extract": "sitc4_ag3_2000_2024",
            },
            {
                "reporterDesc": "Tonga",
                "refYear": 2008,
                "partnerISO": "W00",
                "cmdCode": "001",
                "classificationCode": "S4",
                "freqCode": "A",
                "flowCode": "M",
                "cifvalue__US__": None,
                "fobvalue__US__": None,
                "primaryValue__US__": 5.0,
                "comtrade_extract": "sitc4_ag3_2000_2024",
            },
            {
                "reporterDesc": "Tonga",
                "refYear": 2010,
                "partnerISO": "W00",
                "cmdCode": "001",
                "classificationCode": "S4",
                "freqCode": "A",
                "flowCode": "M",
                "cifvalue__US__": 5.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 5.0,
                "comtrade_extract": "sitc4_ag3_2000_2024",
            },
        ]
    )
    imf_raw = pd.DataFrame(
        [
            {"country": "Fiji, Republic of", "time_period": 2008},
            {"country": "Fiji, Republic of", "time_period": 2013},
            {"country": "Tonga", "time_period": 2008},
            {"country": "Tonga", "time_period": 2010},
            {"country": "Vanuatu", "time_period": 2008},
        ]
    )
    return comtrade_raw, imf_raw


def test_metadata_discrepancy_analysis_builds_tables_not_multi_extract_flags():
    from trade_discrepancy.metadata import run_metadata_discrepancy_analysis

    comtrade_raw, imf_raw = _sample_metadata_frames()
    metadata = run_metadata_discrepancy_analysis(comtrade_raw, imf_raw)
    assert set(metadata) == {
        "metadata_attributes",
        "metadata_coverage",
        "metadata_flags",
        "valuation_completeness",
        "schema_comparison",
        "classification_grain",
        "reporter_coverage",
    }
    flags = set(metadata["metadata_flags"]["flag"])
    assert "multi_extract" not in flags
    assert "gaps_within_span" in flags
    fiji = metadata["metadata_coverage"][
        metadata["metadata_coverage"]["comtrade_country"] == "Fiji"
    ].iloc[0]
    assert fiji["has_comtrade_usa"]
    assert fiji["overlap_years"] == 2
    tonga = metadata["metadata_coverage"][
        metadata["metadata_coverage"]["comtrade_country"] == "Tonga"
    ].iloc[0]
    assert tonga["comtrade_missing_years"] == "2009"
    assert metadata["reporter_coverage"]["status"].eq("imf_only").any()
    assert set(metadata["valuation_completeness"]["field"]) == {"CIF", "FOB", "primary"}


def test_coverage_summary_from_metadata_keeps_overlap_columns():
    from trade_discrepancy.metadata import (
        build_metadata_coverage_by_country,
        coverage_summary_from_metadata,
    )

    comtrade_raw, imf_raw = _sample_metadata_frames()
    coverage = coverage_summary_from_metadata(
        build_metadata_coverage_by_country(comtrade_raw, imf_raw)
    )
    assert "overlap_years" in coverage.columns
    assert "comtrade_missing_years" not in coverage.columns
    fiji = coverage[coverage["country"] == "Fiji, Republic of"].iloc[0]
    assert fiji["overlap_years"] == 2


@pytest.mark.integration
def test_run_analysis_covers_all_dimensions_and_exports(tmp_path):
    from trade_discrepancy.pipeline import ANALYSIS_DIMENSIONS, CORE_OUTPUT_FILES, run_analysis

    results = run_analysis(tmp_path)
    assert results["analysis_dimensions"] == list(ANALYSIS_DIMENSIONS)
    assert results["n_comparable_observations"] == 535
    assert results["n_world_observations"] == 138
    assert "us" in set(results["metrics"]["partner"])
    assert results["metrics"]["year"].min() == 2008
    for filename in CORE_OUTPUT_FILES:
        assert (tmp_path / "csv" / filename).exists()
    assert (tmp_path / "plots" / "scatter_world_totals.png").exists()
    assert (tmp_path / "plots" / "heatmap_median_discrepancy.png").exists()
    assert (tmp_path / "plots" / "layered_values_overview_world.png").exists()
    assert (tmp_path / "plots" / "timeseries_us.png").exists()
    assert not (tmp_path / "plots" / "coverage_overlap_years.png").exists()
    assert not (tmp_path / "plots" / "metadata_concept_comparison.png").exists()
    assert not (tmp_path / "plots" / "layered_values_fiji.png").exists()
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
    from trade_discrepancy.loaders import load_comtrade, load_imf
    from trade_discrepancy.metadata import (
        build_metadata_coverage_by_country,
        coverage_summary_from_metadata,
    )

    coverage = coverage_summary_from_metadata(
        build_metadata_coverage_by_country(load_comtrade(), load_imf())
    )
    assert len(coverage) == len(COMTRADE_TO_IMF_COUNTRY)
    assert coverage["overlap_years"].min() >= 1
    fiji = coverage[coverage["country"] == "Fiji, Republic of"].iloc[0]
    assert fiji["comtrade_year_min"] == 2008
    assert fiji["overlap_years"] == 17
