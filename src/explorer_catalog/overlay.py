"""Copy study overlay CSVs into the explorer catalog. No remote fetch."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from project_paths import PROJECT_ROOT, SRC_DIR

SPAN_TYPES = frozenset({"covid", "gfc", "ramsi"})
EVENTS_CSV_DIR = PROJECT_ROOT / "outputs" / "baci_events" / "csv"
CALENDAR_FALLBACK = SRC_DIR / "event_context" / "pic_event_calendar.csv"
SENTIMENT_CSV = (
    PROJECT_ROOT / "outputs" / "gdelt_sentiment" / "csv" / "gkg_pic_partner_year.csv"
)
NAMED_SENTIMENT_CSV = (
    PROJECT_ROOT / "outputs" / "gdelt_sentiment" / "csv" / "named_pic_partner_year.csv"
)
PRINT_SOURCE = "print_newspaper"
ALLOWED_PARTNERS = frozenset({"aus", "china", "us", "*"})
BILATERAL_PARTNERS = frozenset({"aus", "china", "us"})


def empty_overlay() -> dict:
    return {
        "calendar_status": "missing",
        "aid_status": "missing",
        "disaster_status": "missing",
        "sentiment_status": "missing",
        "calendar": [],
        "aid": [],
        "disasters": [],
        "sentiment": [],
    }


def load_overlay(
    *,
    csv_dir: Path | None = None,
    calendar_path: Path | None = None,
    aid_path: Path | None = None,
    disasters_path: Path | None = None,
    sentiment_path: Path | None = None,
    calendar_fallback: bool = True,
) -> dict:
    """Load overlay arrays from local CSVs only."""
    overlay = empty_overlay()
    directory = csv_dir if csv_dir is not None else EVENTS_CSV_DIR
    calendar_file = calendar_path or (directory / "event_calendar.csv")
    aid_file = aid_path or (directory / "lowy_aid_by_partner.csv")
    disaster_file = disasters_path or (directory / "emdat_by_country_year.csv")

    calendar_rows = _read_calendar(calendar_file)
    if not calendar_rows and calendar_fallback:
        calendar_rows = _read_calendar(CALENDAR_FALLBACK)
    if calendar_rows:
        overlay["calendar"] = calendar_rows
        overlay["calendar_status"] = "present"

    aid_rows = _read_aid(aid_file)
    if aid_rows:
        overlay["aid"] = aid_rows
        overlay["aid_status"] = "present"

    disaster_rows = _read_disasters(disaster_file)
    if disaster_rows:
        overlay["disasters"] = disaster_rows
        overlay["disaster_status"] = "present"

    sentiment_file = sentiment_path if sentiment_path is not None else _default_sentiment_path()
    sentiment_rows = _read_sentiment(sentiment_file)
    if sentiment_rows:
        overlay["sentiment"] = sentiment_rows
        overlay["sentiment_status"] = "present"

    return overlay


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _read_calendar(path: Path) -> list[dict]:
    frame = _read_csv(path)
    if frame.empty:
        return []
    rows: list[dict] = []
    for row in frame.itertuples(index=False):
        partner = str(getattr(row, "partner", "*"))
        if partner not in ALLOWED_PARTNERS:
            continue
        event_type = str(getattr(row, "event_type", ""))
        year_start = int(row.year_start)
        year_end = int(row.year_end)
        encoding = (
            "span"
            if event_type in SPAN_TYPES and year_end > year_start
            else "line"
        )
        rows.append(
            {
                "event_id": str(row.event_id),
                "year_start": year_start,
                "year_end": year_end,
                "country": str(row.country),
                "partner": partner,
                "event_type": event_type,
                "title": str(getattr(row, "title", "")),
                "encoding": encoding,
            }
        )
    return rows


def _read_aid(path: Path) -> list[dict]:
    frame = _read_csv(path)
    if frame.empty or "lowy_spent_usd" not in frame.columns:
        return []
    rows: list[dict] = []
    for row in frame.itertuples(index=False):
        partner = str(row.partner)
        if partner not in BILATERAL_PARTNERS:
            continue
        spent = getattr(row, "lowy_spent_usd", None)
        rows.append(
            {
                "country": str(row.country),
                "year": int(row.year),
                "partner": partner,
                "lowy_spent_usd": None if pd.isna(spent) else float(spent),
            }
        )
    return rows


def _read_disasters(path: Path) -> list[dict]:
    frame = _read_csv(path)
    if frame.empty or "emdat_has_disaster" not in frame.columns:
        return []
    rows: list[dict] = []
    for row in frame.itertuples(index=False):
        has_disaster = int(getattr(row, "emdat_has_disaster", 0) or 0)
        n_events = getattr(row, "emdat_n_events", 0)
        rows.append(
            {
                "country": str(row.country),
                "year": int(row.year),
                "emdat_has_disaster": 1 if has_disaster else 0,
                "emdat_n_events": 0 if pd.isna(n_events) else int(n_events),
            }
        )
    return rows


def _default_sentiment_path() -> Path:
    if SENTIMENT_CSV.is_file():
        return SENTIMENT_CSV
    return NAMED_SENTIMENT_CSV


def _int_field(row: object, name: str) -> int:
    value = getattr(row, name, 0)
    if value is None or pd.isna(value):
        return 0
    return int(value)


def _read_sentiment(path: Path) -> list[dict]:
    """Print-newspaper PIC × partner × year GDELT tone from the sentiment study."""
    frame = _read_csv(path)
    required = {"country", "year", "partner", "mean_gdelt_tone", "n_with_gdelt_tone"}
    if frame.empty or not required.issubset(frame.columns):
        return []
    if "source_class" in frame.columns:
        frame = frame[frame["source_class"] == PRINT_SOURCE]
    rows: list[dict] = []
    for row in frame.itertuples(index=False):
        partner = str(row.partner)
        if partner not in BILATERAL_PARTNERS:
            continue
        tone = getattr(row, "mean_gdelt_tone", None)
        n_tone = getattr(row, "n_with_gdelt_tone", 0)
        n_items = getattr(row, "n_items", 0)
        rows.append(
            {
                "country": str(row.country),
                "year": int(row.year),
                "partner": partner,
                "n_items": 0 if pd.isna(n_items) else int(n_items),
                "n_with_tone": 0 if pd.isna(n_tone) else int(n_tone),
                "mean_tone": None if pd.isna(tone) else float(tone),
                "n_positive": _int_field(row, "n_gdelt_positive"),
                "n_neutral": _int_field(row, "n_gdelt_neutral"),
                "n_negative": _int_field(row, "n_gdelt_negative"),
            }
        )
    return rows
