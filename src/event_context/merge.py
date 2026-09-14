"""Join the calendar, Lowy aid, and EM-DAT onto BACI influence indices."""

import pandas as pd

from event_context.calendar import expand_calendar, panel_event_flags
from event_context.constants import DISPLAY_TO_ISO3, FLAG_TYPES


def _flag_columns() -> list[str]:
    return [f"flag_{name}" for name in FLAG_TYPES]


def merge_calendar(indices: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    flags = panel_event_flags(expand_calendar(calendar))
    merged = indices.merge(flags, on=["country", "year", "partner"], how="left")
    merged["calendar_n_events"] = merged["calendar_n_events"].fillna(0).astype(int)
    merged["calendar_event_ids"] = merged["calendar_event_ids"].fillna("")
    merged["calendar_titles"] = merged["calendar_titles"].fillna("")
    for col in _flag_columns():
        if col not in merged.columns:
            merged[col] = 0
        merged[col] = merged[col].fillna(0).astype(int)
    return merged


def merge_lowy(indices: pd.DataFrame, aid: pd.DataFrame) -> pd.DataFrame:
    if aid.empty:
        for col in (
            "lowy_spent_usd",
            "lowy_committed_usd",
            "lowy_spent_total_usd",
            "lowy_committed_total_usd",
            "lowy_spent_share",
        ):
            indices[col] = pd.NA
        return indices
    return indices.merge(aid, on=["country", "year", "partner"], how="left")


def merge_emdat(indices: pd.DataFrame, disasters: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "country",
        "year",
        "emdat_n_events",
        "emdat_affected",
        "emdat_deaths",
        "emdat_damage_usd",
        "emdat_types",
        "emdat_has_disaster",
    ]
    if disasters.empty:
        for col in cols[2:]:
            indices[col] = 0 if col != "emdat_types" else pd.NA
        indices["emdat_has_disaster"] = 0
        return indices
    keep = [col for col in cols if col in disasters.columns]
    merged = indices.merge(disasters[keep], on=["country", "year"], how="left")
    merged["emdat_n_events"] = merged["emdat_n_events"].fillna(0)
    merged["emdat_affected"] = merged["emdat_affected"].fillna(0)
    merged["emdat_deaths"] = merged["emdat_deaths"].fillna(0)
    merged["emdat_damage_usd"] = merged["emdat_damage_usd"].fillna(0)
    merged["emdat_has_disaster"] = merged["emdat_has_disaster"].fillna(0).astype(int)
    return merged


def merge_all(
    indices: pd.DataFrame,
    calendar: pd.DataFrame,
    aid: pd.DataFrame,
    disasters: pd.DataFrame,
) -> pd.DataFrame:
    """Left-join overlays onto the BACI index panel. Row count is preserved."""
    merged = merge_calendar(indices, calendar)
    merged = merge_lowy(merged, aid)
    merged = merge_emdat(merged, disasters)
    if "iso3" not in merged.columns:
        merged["iso3"] = merged["country"].map(DISPLAY_TO_ISO3)
    return merged.sort_values(["country", "year", "partner"]).reset_index(drop=True)


def coverage_summary(
    merged: pd.DataFrame,
    *,
    lowy_source: str,
    emdat_source: str,
    n_calendar_events: int,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "n_index_rows": len(merged),
                "n_countries": merged["country"].nunique() if not merged.empty else 0,
                "n_calendar_source_events": n_calendar_events,
                "n_rows_with_calendar_event": int((merged["calendar_n_events"] > 0).sum()),
                "n_rows_with_lowy_spent": int(merged["lowy_spent_usd"].notna().sum())
                if "lowy_spent_usd" in merged.columns
                else 0,
                "n_rows_with_emdat_disaster": int((merged["emdat_has_disaster"] > 0).sum())
                if "emdat_has_disaster" in merged.columns
                else 0,
                "lowy_source": lowy_source,
                "emdat_source": emdat_source,
            }
        ]
    )
