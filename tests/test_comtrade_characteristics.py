import pandas as pd

from comtrade_characteristics.pipeline import CORE_OUTPUT_FILES, run_analysis
from comtrade_characteristics.summarize import (
    availability_by_year,
    flow_by_year,
    overview,
    partner_gaps,
    prepare_extract,
    reporter_summary,
    reporter_year_panel,
    value_completeness,
)


def _sample_extract() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reporterDesc": "Fiji",
                "refYear": 2014,
                "flowCode": "M",
                "partnerISO": "AUS",
                "cmdCode": "001",
                "cifvalue__US__": 10.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 10.0,
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2014,
                "flowCode": "M",
                "partnerISO": "CHN",
                "cmdCode": "001",
                "cifvalue__US__": 4.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 4.0,
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2014,
                "flowCode": "M",
                "partnerISO": "USA",
                "cmdCode": "011",
                "cifvalue__US__": 2.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 2.0,
            },
            {
                "reporterDesc": "Fiji",
                "refYear": 2014,
                "flowCode": "M",
                "partnerISO": "W00",
                "cmdCode": "001",
                "cifvalue__US__": 16.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 16.0,
            },
            {
                "reporterDesc": "Kiribati",
                "refYear": 2014,
                "flowCode": "X",
                "partnerISO": "AUS",
                "cmdCode": "034",
                "cifvalue__US__": None,
                "fobvalue__US__": 5.0,
                "primaryValue__US__": 5.0,
            },
            {
                "reporterDesc": "Kiribati",
                "refYear": 2014,
                "flowCode": "X",
                "partnerISO": "USA",
                "cmdCode": "034",
                "cifvalue__US__": None,
                "fobvalue__US__": 1.0,
                "primaryValue__US__": 1.0,
            },
            {
                "reporterDesc": "Kiribati",
                "refYear": 2014,
                "flowCode": "X",
                "partnerISO": "W00",
                "cmdCode": "034",
                "cifvalue__US__": None,
                "fobvalue__US__": 6.0,
                "primaryValue__US__": 6.0,
            },
            {
                "reporterDesc": "Solomon Isds",
                "refYear": 2015,
                "flowCode": "M",
                "partnerISO": "W00",
                "cmdCode": "001",
                "cifvalue__US__": 8.0,
                "fobvalue__US__": None,
                "primaryValue__US__": 8.0,
            },
        ]
    )


def test_prepare_extract_maps_display_names_and_years():
    working = prepare_extract(_sample_extract())
    assert set(working["country"]) == {"Fiji", "Kiribati", "Solomon Islands"}
    assert set(working["year"]) == {2014, 2015}


def test_availability_by_year_fills_requested_empty_years():
    working = prepare_extract(_sample_extract())
    availability = availability_by_year(working, years=(2013, 2014, 2015))
    assert list(availability["year"]) == [2013, 2014, 2015]
    assert list(availability["n_records"]) == [0, 7, 1]
    assert availability.loc[0, "reporters"] == ""
    assert availability.loc[1, "n_reporters"] == 2
    assert "Fiji" in availability.loc[1, "reporters"]


def test_reporter_year_panel_covers_requested_grid():
    working = prepare_extract(_sample_extract())
    reporters = ("Fiji", "Kiribati", "Nauru")
    panel = reporter_year_panel(working, reporters=reporters, years=(2014, 2015))
    assert len(panel) == 6
    fiji_2014 = panel[(panel["country"] == "Fiji") & (panel["year"] == 2014)].iloc[0]
    nauru_2014 = panel[(panel["country"] == "Nauru") & (panel["year"] == 2014)].iloc[0]
    assert fiji_2014["present"] == 1
    assert fiji_2014["n_records"] == 4
    assert nauru_2014["present"] == 0
    assert nauru_2014["iso3"] == "NRU"


def test_reporter_summary_includes_absent_requested_reporters():
    working = prepare_extract(_sample_extract())
    summary = reporter_summary(
        working,
        reporters=("Fiji", "Nauru"),
        years=(2014, 2015),
    )
    fiji = summary[summary["country"] == "Fiji"].iloc[0]
    nauru = summary[summary["country"] == "Nauru"].iloc[0]
    assert bool(fiji["observed"]) is True
    assert fiji["n_years"] == 1
    assert fiji["year_share"] == 0.5
    assert bool(nauru["observed"]) is False
    assert nauru["n_records"] == 0
    assert pd.isna(nauru["year_min"])


def test_partner_gaps_flags_missing_china_exports():
    working = prepare_extract(_sample_extract())
    gaps = partner_gaps(working)
    assert len(gaps) == 2
    kiribati = gaps[gaps["country"] == "Kiribati"].iloc[0]
    assert kiribati["missing_partners"] == "CHN"
    assert kiribati["flow"] == "export"


def test_value_completeness_by_flow():
    working = prepare_extract(_sample_extract())
    completeness = value_completeness(working)
    imports = completeness[completeness["flowCode"] == "M"].iloc[0]
    exports = completeness[completeness["flowCode"] == "X"].iloc[0]
    assert imports["cifvalue__US___share"] == 1.0
    assert exports["fobvalue__US___share"] == 1.0
    assert exports["cifvalue__US___share"] == 0.0


def test_overview_computes_requested_versus_observed_coverage():
    working = prepare_extract(_sample_extract())
    table = overview(
        working,
        reporters=("Fiji", "Kiribati", "Nauru"),
        years=(2014, 2015),
    )
    values = dict(zip(table["metric"], table["value"]))
    assert values["n_records"] == 8
    assert values["n_years_observed"] == 2
    assert values["n_reporters_observed"] == 2
    assert values["n_reporters_absent"] == 1
    assert values["n_reporter_years_requested"] == 6
    assert values["n_reporter_years_observed"] == 2
    assert values["reporter_year_coverage"] == 0.3333


def test_flow_by_year_labels_import_and_export():
    working = prepare_extract(_sample_extract())
    flows = flow_by_year(working)
    assert set(flows["flow"]) == {"import", "export"}
    assert int(flows.loc[flows["flowCode"] == "X", "n_records"].sum()) == 3


def test_pipeline_writes_csv_tables(tmp_path):
    extract_dir = tmp_path / "data"
    extract_dir.mkdir()
    _sample_extract().to_csv(extract_dir / "TradeData_sitc4_ag3_2000_2024.csv", index=False)
    results = run_analysis(
        output_dir=tmp_path / "out",
        extract_dir=extract_dir,
        extract_filename="TradeData_sitc4_ag3_2000_2024.csv",
    )
    csv_dir = tmp_path / "out" / "csv"
    for filename in CORE_OUTPUT_FILES:
        assert (csv_dir / filename).exists()
    assert results["n_records"] == 8
    assert results["n_reporters_observed"] == 3
    assert results["year_min"] == 2014
    assert results["year_max"] == 2015
    assert results["n_years_observed"] == 2
    assert not (tmp_path / "out" / "plots").exists()
