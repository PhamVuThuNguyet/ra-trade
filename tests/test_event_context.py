"""Unit tests for the PIC event / Lowy / EM-DAT overlay on BACI indices."""

from pathlib import Path

import pandas as pd
import pytest

from event_context.calendar import expand_calendar, load_calendar, panel_event_flags
from event_context.constants import CALENDAR_PATH, FLAG_TYPES
from event_context.emdat import aggregate_emdat
from event_context.lowy import aggregate_pacific_links, aggregate_pam_rows, map_donor, map_recipient
from event_context.merge import merge_all
from event_context.pipeline import run_overlay
from event_context.visualize import disaster_years, event_label, generate_overlay_plots


def _indices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "country": "Solomon Islands",
                "year": 2019,
                "partner": "china",
                "import_index": 0.23,
                "export_index": 0.65,
            },
            {
                "country": "Solomon Islands",
                "year": 2019,
                "partner": "aus",
                "import_index": 0.15,
                "export_index": 0.05,
            },
            {
                "country": "Fiji",
                "year": 2016,
                "partner": "aus",
                "import_index": 0.20,
                "export_index": 0.14,
            },
            {
                "country": "Niue",
                "year": 2010,
                "partner": "us",
                "import_index": 0.02,
                "export_index": 0.01,
            },
        ]
    )


def test_load_calendar_validates_bundled_file():
    calendar = load_calendar()
    assert not calendar.empty
    assert calendar["event_id"].is_unique
    assert set(calendar["event_type"]) <= set(FLAG_TYPES)


def test_expand_wildcard_covers_all_pics_and_partners():
    calendar = pd.DataFrame(
        [
            {
                "event_id": "covid_2020",
                "year_start": 2020,
                "year_end": 2020,
                "country": "*",
                "partner": "*",
                "event_type": "covid",
                "title": "COVID-19",
                "notes": "",
            }
        ]
    )
    expanded = expand_calendar(calendar)
    assert len(expanded) == 14 * 3
    assert set(expanded["partner"]) == {"aus", "china", "us"}


def test_pacer_plus_flags_only_australia():
    calendar = load_calendar(CALENDAR_PATH)
    flags = panel_event_flags(expand_calendar(calendar))
    slb_2021 = flags[
        (flags["country"] == "Solomon Islands") & (flags["year"] == 2021)
    ]
    aus = slb_2021[slb_2021["partner"] == "aus"].iloc[0]
    china = slb_2021[slb_2021["partner"] == "china"].iloc[0]
    assert aus["flag_pacer_plus"] == 1
    assert china["flag_pacer_plus"] == 0
    assert china["flag_diplomatic_switch"] == 1


def test_map_recipient_and_donor():
    assert map_recipient("SB") == "Solomon Islands"
    assert map_recipient("FSM") == "Micronesia"
    assert map_recipient("CK", "Cook Islands") == "Cook Islands"
    assert map_donor("AU") == "aus"
    assert map_donor("CN", "China") == "china"
    assert map_donor("US") == "us"
    assert map_donor("NZ") is None


def test_aggregate_pam_rows_splits_spent_and_committed():
    raw = pd.DataFrame(
        [
            _pam_row("FJ", "AU", "SPE", 2018, 100),
            _pam_row("FJ", "AU", "COM", 2018, 150),
            _pam_row("FJ", "NZ", "SPE", 2018, 50),
            _pam_row("FJ", "CN", "SPE", 2018, 25),
        ]
    )
    panel = aggregate_pam_rows(raw)
    aus = panel[(panel["partner"] == "aus")].iloc[0]
    assert aus["lowy_spent_usd"] == pytest.approx(100)
    assert aus["lowy_committed_usd"] == pytest.approx(150)
    assert aus["lowy_spent_total_usd"] == pytest.approx(175)
    assert aus["lowy_spent_share"] == pytest.approx(100 / 175)


def _pam_row(geo, donor, spent, year, value) -> dict:
    return {
        "FREQ": "A",
        "GEO_PICT": geo,
        "INDICATOR": "TRVAL",
        "DONOR": donor,
        "COMMITTED_SPENT": spent,
        "FLOW_TYPE": "_T",
        "TIME_PERIOD": year,
        "OBS_VALUE": value,
    }


def test_aggregate_pacific_links_fallback():
    spent = pd.DataFrame(
        [
            {
                "pacific_code": "FJ",
                "pacific_name": "Fiji",
                "counterpart_code": "AU",
                "counterpart_name": "Australia",
                "year": 2011,
                "value_usd": 40.0,
            }
        ]
    )
    committed = spent.copy()
    committed["aid_committed_usd"] = 80.0
    committed = committed.drop(columns=["value_usd"])
    panel = aggregate_pacific_links(spent, committed)
    assert panel.iloc[0]["lowy_spent_usd"] == pytest.approx(40)
    assert panel.iloc[0]["lowy_committed_usd"] == pytest.approx(80)


def test_aggregate_emdat_skips_hxl_and_filters_pics():
    raw = pd.DataFrame(
        [
            {
                "Year": "#date+occurred",
                "ISO": "#country+code",
                "Total Events": "#frequency",
                "Total Affected": "#affected+ind",
                "Total Deaths": "#affected+ind+killed",
                "Total Damage (USD, original)": "",
                "Disaster Type": "#cause+type",
            },
            {
                "Year": 2015,
                "ISO": "VUT",
                "Total Events": 2,
                "Total Affected": 1000,
                "Total Deaths": 11,
                "Total Damage (USD, original)": 500,
                "Disaster Type": "Storm",
            },
            {
                "Year": 2015,
                "ISO": "VUT",
                "Total Events": 1,
                "Total Affected": 200,
                "Total Deaths": 0,
                "Total Damage (USD, original)": 50,
                "Disaster Type": "Flood",
            },
            {
                "Year": 2015,
                "ISO": "AUS",
                "Total Events": 9,
                "Total Affected": 1,
                "Total Deaths": 1,
                "Total Damage (USD, original)": 1,
                "Disaster Type": "Storm",
            },
        ]
    )
    panel = aggregate_emdat(raw)
    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["country"] == "Vanuatu"
    assert row["emdat_n_events"] == pytest.approx(3)
    assert row["emdat_has_disaster"] == 1
    assert set(row["emdat_types"].split(";")) == {"Flood", "Storm"}


def test_merge_preserves_index_rows_and_flags():
    calendar = load_calendar()
    aid = pd.DataFrame(
        [
            {
                "country": "Solomon Islands",
                "year": 2019,
                "partner": "china",
                "lowy_spent_usd": 12.0,
                "lowy_committed_usd": 20.0,
                "lowy_spent_total_usd": 30.0,
                "lowy_committed_total_usd": 40.0,
                "lowy_spent_share": 0.4,
            }
        ]
    )
    disasters = pd.DataFrame(
        [
            {
                "country": "Fiji",
                "year": 2016,
                "emdat_n_events": 1,
                "emdat_affected": 40_000,
                "emdat_deaths": 44,
                "emdat_damage_usd": 1.0,
                "emdat_types": "Storm",
                "emdat_has_disaster": 1,
            }
        ]
    )
    merged = merge_all(_indices(), calendar, aid, disasters)
    assert len(merged) == 4
    slb_chn = merged[
        (merged["country"] == "Solomon Islands") & (merged["partner"] == "china")
    ].iloc[0]
    assert slb_chn["flag_diplomatic_switch"] == 1
    assert slb_chn["lowy_spent_usd"] == pytest.approx(12)
    fiji = merged[merged["country"] == "Fiji"].iloc[0]
    assert fiji["emdat_has_disaster"] == 1
    niue = merged[merged["country"] == "Niue"].iloc[0]
    assert niue["calendar_n_events"] == 0
    assert pd.isna(niue["lowy_spent_usd"])
    assert niue["emdat_n_events"] == 0


def test_pipeline_writes_outputs(tmp_path: Path):
    output_dir = tmp_path / "out"
    results = run_overlay(
        output_dir=output_dir,
        indices=_indices(),
        fetch_remote=False,
        aid=pd.DataFrame(),
        disasters=pd.DataFrame(),
        write_sidecar=False,
    )
    csv_dir = Path(results["csv_dir"])
    merged = pd.read_csv(csv_dir / "indices_baci.csv")
    assert len(merged) == 4
    assert "flag_covid" in merged.columns
    assert results["lowy_source"] == "supplied"
    for name in (
        "event_calendar.csv",
        "lowy_aid_by_partner.csv",
        "emdat_by_country_year.csv",
        "indices_baci.csv",
        "coverage_summary.csv",
    ):
        assert (csv_dir / name).exists()
    plots_dir = Path(results["plots_dir"])
    assert results["plots"]
    for path in results["plots"]:
        assert Path(path).exists()
    assert (plots_dir / "worked_examples_import_index_events.png").exists()


def test_disaster_years_filters_country():
    disasters = pd.DataFrame(
        [
            {"country": "Fiji", "year": 2016, "emdat_has_disaster": 1},
            {"country": "Fiji", "year": 2010, "emdat_has_disaster": 0},
            {"country": "Tonga", "year": 2022, "emdat_has_disaster": 1},
        ]
    )
    assert disaster_years(disasters, "Fiji") == [2016]
    assert disaster_years(disasters, "Niue") == []


def test_event_label_uses_short_type_or_truncated_title():
    calendar = load_calendar()
    pacer = calendar[calendar["event_type"] == "pacer_plus"].iloc[0]
    assert event_label(pacer) == "PACER+"
    long = calendar[calendar["event_type"] == "diplomatic_switch"].iloc[0]
    label = event_label(long, max_chars=12)
    assert len(label) <= 12


def test_generate_overlay_plots_writes_pngs(tmp_path: Path):
    calendar = load_calendar()
    disasters = pd.DataFrame(
        [{"country": "Fiji", "year": 2016, "emdat_has_disaster": 1, "emdat_n_events": 1}]
    )
    paths = generate_overlay_plots(_indices(), calendar, disasters, tmp_path)
    assert paths
    assert all(path.exists() and path.suffix == ".png" for path in paths)
