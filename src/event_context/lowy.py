"""Lowy Pacific Aid Map via Pacific Data Hub SDMX (DF_PAM)."""

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from baci.constants import PIC_DISPLAY_NAMES
from event_context.constants import (
    DONOR_CODE_TO_PARTNER,
    DONOR_NAME_TO_PARTNER,
    ISO2_TO_DISPLAY,
    ISO3_TO_DISPLAY,
    LOWY_AGGREGATE_DONORS,
    LOWY_RAW_CSV,
    PDH_AGENCY,
    PDH_BASE_URL,
    PDH_DATAFLOW,
)
from event_context.fetch import get_text

SDMX_KEY = "A..TRVAL..SPE+COM._T"
PACIFIC_LINKS_SPENT_URL = (
    "https://raw.githubusercontent.com/J-King-Dottie/pacific-links/main/"
    "dashboard/public/data/aid_by_donor_year.csv"
)
PACIFIC_LINKS_COMMITTED_URL = (
    "https://raw.githubusercontent.com/J-King-Dottie/pacific-links/main/"
    "dashboard/public/data/aid_committed_by_donor_year.csv"
)


def pam_csv_url(*, start_period: int = 2002, end_period: int = 2024) -> str:
    return (
        f"{PDH_BASE_URL}/data/{PDH_AGENCY},{PDH_DATAFLOW},1.0/{SDMX_KEY}"
        f"?dimensionAtObservation=AllDimensions&format=csvfile"
        f"&startPeriod={start_period}&endPeriod={end_period}"
    )


def map_recipient(code: str, name: str | None = None) -> str | None:
    """Map a PDH/Lowy recipient code or name to a BACI display country."""
    token = str(code).strip()
    if token in ISO2_TO_DISPLAY:
        return ISO2_TO_DISPLAY[token]
    if token in ISO3_TO_DISPLAY:
        return ISO3_TO_DISPLAY[token]
    if token in PIC_DISPLAY_NAMES:
        return token
    label = (name or "").strip()
    if label in PIC_DISPLAY_NAMES:
        return label
    if label == "Federated States of Micronesia":
        return "Micronesia"
    return None


def map_donor(code: str, name: str | None = None) -> str | None:
    """Map a donor code or name to aus / china / us, else None."""
    token = str(code).strip().upper()
    if token in DONOR_CODE_TO_PARTNER:
        return DONOR_CODE_TO_PARTNER[token]
    label = (name or "").strip().lower()
    return DONOR_NAME_TO_PARTNER.get(label)


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def aggregate_pam_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """Country-year-partner spent/committed USD from DF_PAM observation rows."""
    working = raw.copy()
    working = working[
        (working["FREQ"] == "A")
        & (working["INDICATOR"] == "TRVAL")
        & (working["COMMITTED_SPENT"].isin(["SPE", "COM"]))
        & (working["FLOW_TYPE"] == "_T")
        & (~working["DONOR"].isin(LOWY_AGGREGATE_DONORS))
        & (working["GEO_PICT"] != "_T")
    ]
    working["country"] = [
        map_recipient(code) for code in working["GEO_PICT"]
    ]
    working = working.dropna(subset=["country"])
    working["year"] = working["TIME_PERIOD"].astype(int)
    working["value"] = _numeric(working["OBS_VALUE"])
    spent = working[working["COMMITTED_SPENT"] == "SPE"]
    committed = working[working["COMMITTED_SPENT"] == "COM"]
    partner_spent = _partner_sums(spent, "lowy_spent_usd")
    partner_committed = _partner_sums(committed, "lowy_committed_usd")
    totals_spent = _country_year_sums(spent, "lowy_spent_total_usd")
    totals_committed = _country_year_sums(committed, "lowy_committed_total_usd")
    panel = partner_spent.merge(
        partner_committed, on=["country", "year", "partner"], how="outer"
    )
    panel = panel.merge(totals_spent, on=["country", "year"], how="left")
    panel = panel.merge(totals_committed, on=["country", "year"], how="left")
    panel["lowy_spent_share"] = panel["lowy_spent_usd"] / panel["lowy_spent_total_usd"]
    return panel.sort_values(["country", "year", "partner"]).reset_index(drop=True)


def _partner_sums(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    tagged = frame.copy()
    tagged["partner"] = [
        map_donor(code) for code in tagged["DONOR"]
    ]
    tagged = tagged.dropna(subset=["partner"])
    return (
        tagged.groupby(["country", "year", "partner"], as_index=False)["value"]
        .sum()
        .rename(columns={"value": value_col})
    )


def _country_year_sums(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    return (
        frame.groupby(["country", "year"], as_index=False)["value"]
        .sum()
        .rename(columns={"value": value_col})
    )


def aggregate_pacific_links(
    spent: pd.DataFrame,
    committed: pd.DataFrame,
) -> pd.DataFrame:
    """Fallback: pacific-links country-donor-year extracts (still Lowy-sourced)."""
    spent_panel = _links_to_partner(spent, "lowy_spent_usd")
    committed_panel = _links_to_partner(committed, "lowy_committed_usd")
    spent_total = _links_country_year_total(spent, "lowy_spent_total_usd")
    committed_total = _links_country_year_total(committed, "lowy_committed_total_usd")
    panel = spent_panel.merge(
        committed_panel, on=["country", "year", "partner"], how="outer"
    )
    panel = panel.merge(spent_total, on=["country", "year"], how="left")
    panel = panel.merge(committed_total, on=["country", "year"], how="left")
    panel["lowy_spent_share"] = panel["lowy_spent_usd"] / panel["lowy_spent_total_usd"]
    return panel.sort_values(["country", "year", "partner"]).reset_index(drop=True)


def _links_to_partner(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    working = frame.copy()
    code_col = "pacific_code" if "pacific_code" in working.columns else "recipient_code"
    name_col = "pacific_name" if "pacific_name" in working.columns else "recipient_name"
    donor_col = (
        "counterpart_code" if "counterpart_code" in working.columns else "donor_code"
    )
    donor_name_col = (
        "counterpart_name" if "counterpart_name" in working.columns else "donor_name"
    )
    value_src = "value_usd" if "value_usd" in working.columns else "aid_spent_usd"
    if value_src not in working.columns and "aid_committed_usd" in working.columns:
        value_src = "aid_committed_usd"
    working["country"] = [
        map_recipient(code, name)
        for code, name in zip(working[code_col], working[name_col])
    ]
    working["partner"] = [
        map_donor(code, name)
        for code, name in zip(working[donor_col], working[donor_name_col])
    ]
    working = working.dropna(subset=["country", "partner"])
    working["year"] = working["year"].astype(int)
    working[value_col] = _numeric(working[value_src])
    return working.groupby(["country", "year", "partner"], as_index=False)[value_col].sum()


def _links_country_year_total(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    working = frame.copy()
    code_col = "pacific_code" if "pacific_code" in working.columns else "recipient_code"
    name_col = "pacific_name" if "pacific_name" in working.columns else "recipient_name"
    value_src = "value_usd" if "value_usd" in working.columns else "aid_spent_usd"
    if value_src not in working.columns and "aid_committed_usd" in working.columns:
        value_src = "aid_committed_usd"
    working["country"] = [
        map_recipient(code, name)
        for code, name in zip(working[code_col], working[name_col])
    ]
    working = working.dropna(subset=["country"])
    working["year"] = working["year"].astype(int)
    working[value_col] = _numeric(working[value_src])
    return working.groupby(["country", "year"], as_index=False)[value_col].sum()


def load_lowy_aid(
    raw_path: Path = LOWY_RAW_CSV,
    *,
    fetch_remote: bool = True,
) -> tuple[pd.DataFrame, str]:
    """
    Return (country-year-partner aid panel, source label).

    Prefers live PDH SDMX DF_PAM (Lowy). Falls back to the pacific-links
    Lowy extract if SDMX is unavailable.
    """
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        return aggregate_pam_rows(raw), "lowy_pdh_cache"
    if fetch_remote:
        try:
            text = get_text(pam_csv_url(), timeout=180)
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(text, encoding="utf-8")
            return aggregate_pam_rows(pd.read_csv(StringIO(text))), "lowy_pdh_sdmx"
        except (OSError, ValueError, KeyError, pd.errors.ParserError, requests.RequestException):
            try:
                spent = pd.read_csv(StringIO(get_text(PACIFIC_LINKS_SPENT_URL)))
                committed = pd.read_csv(StringIO(get_text(PACIFIC_LINKS_COMMITTED_URL)))
                return aggregate_pacific_links(spent, committed), "lowy_pacific_links"
            except (OSError, ValueError, pd.errors.ParserError, requests.RequestException):
                return pd.DataFrame(columns=_empty_lowy_columns()), "lowy_missing"
    return pd.DataFrame(columns=_empty_lowy_columns()), "lowy_missing"


def _empty_lowy_columns() -> list[str]:
    return [
        "country",
        "year",
        "partner",
        "lowy_spent_usd",
        "lowy_committed_usd",
        "lowy_spent_total_usd",
        "lowy_committed_total_usd",
        "lowy_spent_share",
    ]
