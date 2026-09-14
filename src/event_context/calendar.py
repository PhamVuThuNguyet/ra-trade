"""Hand-coded PIC policy and shock calendar."""

from pathlib import Path

import pandas as pd

from baci.constants import PIC_DISPLAY_NAMES
from event_context.constants import (
    ALL_COUNTRIES,
    ALL_PARTNERS,
    BACI_YEAR_MAX,
    BACI_YEAR_MIN,
    CALENDAR_PATH,
    FLAG_TYPES,
)
from trade_influence.constants import BILATERAL_PARTNERS

REQUIRED_COLUMNS = (
    "event_id",
    "year_start",
    "year_end",
    "country",
    "partner",
    "event_type",
    "title",
    "notes",
)


def load_calendar(path: Path = CALENDAR_PATH) -> pd.DataFrame:
    """Load the source event list and check country/partner/type codes."""
    frame = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise KeyError(f"Event calendar missing columns: {missing}")
    frame["year_start"] = frame["year_start"].astype(int)
    frame["year_end"] = frame["year_end"].astype(int)
    if (frame["year_end"] < frame["year_start"]).any():
        raise ValueError("Event calendar has year_end before year_start")
    allowed_countries = {ALL_COUNTRIES, *PIC_DISPLAY_NAMES}
    bad_countries = sorted(set(frame["country"]) - allowed_countries)
    if bad_countries:
        raise ValueError(f"Unknown calendar countries: {bad_countries}")
    allowed_partners = {ALL_PARTNERS, *BILATERAL_PARTNERS}
    bad_partners = sorted(set(frame["partner"]) - allowed_partners)
    if bad_partners:
        raise ValueError(f"Unknown calendar partners: {bad_partners}")
    bad_types = sorted(set(frame["event_type"]) - set(FLAG_TYPES))
    if bad_types:
        raise ValueError(f"Unknown calendar event_type values: {bad_types}")
    return frame[list(REQUIRED_COLUMNS)].copy()


def expand_calendar(
    calendar: pd.DataFrame,
    *,
    year_min: int = BACI_YEAR_MIN,
    year_max: int = BACI_YEAR_MAX,
) -> pd.DataFrame:
    """Expand wildcards into country-year-partner rows overlapping the BACI window."""
    rows: list[dict] = []
    for event in calendar.itertuples(index=False):
        start = max(int(event.year_start), year_min)
        end = min(int(event.year_end), year_max)
        if end < start:
            continue
        countries = (
            PIC_DISPLAY_NAMES
            if event.country == ALL_COUNTRIES
            else (event.country,)
        )
        partners = (
            BILATERAL_PARTNERS
            if event.partner == ALL_PARTNERS
            else (event.partner,)
        )
        for year in range(start, end + 1):
            for country in countries:
                for partner in partners:
                    rows.append(
                        {
                            "country": country,
                            "year": year,
                            "partner": partner,
                            "event_id": event.event_id,
                            "event_type": event.event_type,
                            "title": event.title,
                            "notes": event.notes,
                        }
                    )
    if not rows:
        return pd.DataFrame(
            columns=[
                "country",
                "year",
                "partner",
                "event_id",
                "event_type",
                "title",
                "notes",
            ]
        )
    return pd.DataFrame(rows).sort_values(
        ["country", "year", "partner", "event_id"]
    ).reset_index(drop=True)


def panel_event_flags(expanded: pd.DataFrame) -> pd.DataFrame:
    """One row per country-year-partner with dummy flags and joined titles."""
    if expanded.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "year",
                "partner",
                "calendar_n_events",
                "calendar_event_ids",
                "calendar_titles",
                *[f"flag_{name}" for name in FLAG_TYPES],
            ]
        )
    grouped = expanded.groupby(["country", "year", "partner"], as_index=False)
    panel = grouped.agg(
        calendar_n_events=("event_id", "nunique"),
        calendar_event_ids=("event_id", lambda ids: ";".join(sorted(ids))),
        calendar_titles=("title", lambda titles: "; ".join(dict.fromkeys(titles))),
    )
    type_flags = (
        expanded.assign(present=1)
        .pivot_table(
            index=["country", "year", "partner"],
            columns="event_type",
            values="present",
            aggfunc="max",
            fill_value=0,
        )
        .reset_index()
    )
    type_flags.columns.name = None
    panel = panel.merge(type_flags, on=["country", "year", "partner"], how="left")
    for name in FLAG_TYPES:
        if name in panel.columns:
            panel[f"flag_{name}"] = panel.pop(name).fillna(0).astype(int)
        else:
            panel[f"flag_{name}"] = 0
    flag_cols = [f"flag_{name}" for name in FLAG_TYPES]
    return panel[
        [
            "country",
            "year",
            "partner",
            "calendar_n_events",
            "calendar_event_ids",
            "calendar_titles",
            *flag_cols,
        ]
    ]
