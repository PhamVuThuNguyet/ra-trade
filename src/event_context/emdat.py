"""EM-DAT country profiles from HDX (annual disaster totals)."""

from pathlib import Path

import pandas as pd

from event_context.constants import (
    BACI_YEAR_MAX,
    BACI_YEAR_MIN,
    DISPLAY_TO_ISO3,
    EMDAT_HDX_URL,
    EMDAT_RAW_XLSX,
    ISO3_TO_DISPLAY,
)
from event_context.fetch import download_file

YEAR_COL = "Year"
ISO_COL = "ISO"
EVENTS_COL = "Total Events"
AFFECTED_COL = "Total Affected"
DEATHS_COL = "Total Deaths"
DAMAGE_COL = "Total Damage (USD, original)"
TYPE_COL = "Disaster Type"


def _read_profiles(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=0)
    if YEAR_COL not in raw.columns:
        raw = pd.read_excel(path, header=1)
    return raw


def aggregate_emdat(raw: pd.DataFrame) -> pd.DataFrame:
    """Country-year disaster counts for the 14 PICs."""
    working = raw.copy()
    working.columns = [str(col).strip() for col in working.columns]
    if YEAR_COL not in working.columns or ISO_COL not in working.columns:
        raise KeyError(f"EM-DAT file missing Year/ISO columns: {list(working.columns)}")
    working = working[pd.to_numeric(working[YEAR_COL], errors="coerce").notna()]
    working["year"] = working[YEAR_COL].astype(int)
    working["iso3"] = working[ISO_COL].astype(str).str.upper()
    working["country"] = working["iso3"].map(ISO3_TO_DISPLAY)
    working = working.dropna(subset=["country"])
    working[EVENTS_COL] = pd.to_numeric(working.get(EVENTS_COL), errors="coerce")
    working[AFFECTED_COL] = pd.to_numeric(working.get(AFFECTED_COL), errors="coerce")
    working[DEATHS_COL] = pd.to_numeric(working.get(DEATHS_COL), errors="coerce")
    damage_col = DAMAGE_COL if DAMAGE_COL in working.columns else None
    if damage_col is None:
        matches = [col for col in working.columns if col.startswith("Total Damage")]
        damage_col = matches[0] if matches else None
    working["damage"] = (
        pd.to_numeric(working[damage_col], errors="coerce") if damage_col else 0.0
    )
    type_col = TYPE_COL if TYPE_COL in working.columns else None
    grouped = working.groupby(["country", "year", "iso3"], as_index=False).agg(
        emdat_n_events=(EVENTS_COL, "sum"),
        emdat_affected=(AFFECTED_COL, "sum"),
        emdat_deaths=(DEATHS_COL, "sum"),
        emdat_damage_usd=("damage", "sum"),
    )
    if type_col:
        types = (
            working.dropna(subset=[type_col])
            .groupby(["country", "year"])[type_col]
            .agg(lambda values: ";".join(sorted(set(map(str, values)))))
            .reset_index(name="emdat_types")
        )
        grouped = grouped.merge(types, on=["country", "year"], how="left")
    else:
        grouped["emdat_types"] = pd.NA
    grouped["emdat_has_disaster"] = (grouped["emdat_n_events"] > 0).astype(int)
    grouped["iso3"] = grouped["country"].map(DISPLAY_TO_ISO3)
    grouped = grouped[
        (grouped["year"] >= BACI_YEAR_MIN) & (grouped["year"] <= BACI_YEAR_MAX)
    ]
    return grouped.sort_values(["country", "year"]).reset_index(drop=True)


def load_emdat(
    raw_path: Path = EMDAT_RAW_XLSX,
    *,
    fetch_remote: bool = True,
) -> tuple[pd.DataFrame, str]:
    """Return (country-year disaster panel, source label)."""
    if not raw_path.exists() and fetch_remote:
        download_file(EMDAT_HDX_URL, raw_path, timeout=120)
    if not raw_path.exists():
        return pd.DataFrame(columns=_empty_columns()), "emdat_missing"
    return aggregate_emdat(_read_profiles(raw_path)), "emdat_hdx"


def _empty_columns() -> list[str]:
    return [
        "country",
        "year",
        "iso3",
        "emdat_n_events",
        "emdat_affected",
        "emdat_deaths",
        "emdat_damage_usd",
        "emdat_types",
        "emdat_has_disaster",
    ]
