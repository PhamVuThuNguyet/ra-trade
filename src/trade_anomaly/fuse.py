"""Multi-scale fusion into Watch / Alert / Critical attention tiers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from trade_anomaly.constants import (
    PERSISTENCE_YEARS,
    STRUCTURAL_WINDOWS,
    TIER_ALERT,
    TIER_CRITICAL,
    TIER_NONE,
    TIER_WATCH,
    TYPE_LEVEL_SHOCK,
    TYPE_NONE,
    TYPE_STRUCTURAL_BREAK,
    TYPE_UNCERTAIN,
    ULTRA_SHORT_WINDOW,
    Z_ALERT,
    Z_CRITICAL,
    Z_WATCH,
)


def _max_abs_z_by_window(group: pd.DataFrame) -> dict[int, float]:
    """Max |z| across models for each window in a series-year group."""
    out: dict[int, float] = {}
    for window, frame in group.groupby("window"):
        out[int(window)] = float(frame["abs_z"].max())
    return out


def _count_structural_above(z_by_window: dict[int, float], threshold: float) -> int:
    return sum(
        1
        for w in STRUCTURAL_WINDOWS
        if z_by_window.get(w, 0.0) >= threshold
    )


def _ultra_short_above(z_by_window: dict[int, float], threshold: float) -> bool:
    return z_by_window.get(ULTRA_SHORT_WINDOW, 0.0) >= threshold


def classify_tier(z_by_window: dict[int, float]) -> str:
    """
    Tier rules:
      Watch: any scale |z| >= 2.0
      Alert: >=2 structural scales at 2.5, OR ultra-short + >=1 structural at 2.5
      Critical: >=2 structural at 3.0 (ultra-short alone never Critical)
    """
    structural_crit = _count_structural_above(z_by_window, Z_CRITICAL)
    structural_alert = _count_structural_above(z_by_window, Z_ALERT)
    any_watch = any(z >= Z_WATCH for z in z_by_window.values())

    if structural_crit >= 2:
        return TIER_CRITICAL
    if structural_alert >= 2:
        return TIER_ALERT
    if _ultra_short_above(z_by_window, Z_ALERT) and structural_alert >= 1:
        return TIER_ALERT
    if any_watch:
        return TIER_WATCH
    return TIER_NONE


def classify_type(z_by_window: dict[int, float], tier: str) -> str:
    if tier == TIER_NONE:
        return TYPE_NONE

    short_hot = _ultra_short_above(z_by_window, Z_WATCH)
    structural_hot = _count_structural_above(z_by_window, Z_WATCH)
    medium_long_hot = sum(
        1 for w in (5, 7) if z_by_window.get(w, 0.0) >= Z_WATCH
    )

    if short_hot and structural_hot == 0:
        return TYPE_LEVEL_SHOCK
    if medium_long_hot >= 1 and structural_hot >= 1:
        return TYPE_STRUCTURAL_BREAK
    if short_hot and structural_hot >= 1:
        return TYPE_UNCERTAIN
    if structural_hot >= 1:
        return TYPE_STRUCTURAL_BREAK
    return TYPE_LEVEL_SHOCK if short_hot else TYPE_UNCERTAIN


def fuse_scores(scores: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse model×window scores to series×year alerts with tier and type.

    Also upgrades Alert → Critical when structural |z| stays elevated for
    ``PERSISTENCE_YEARS`` consecutive years.
    """
    if scores.empty:
        return pd.DataFrame(
            columns=[
                "series_id",
                "country",
                "partner",
                "flow",
                "metric",
                "year",
                "tier",
                "anomaly_type",
                "max_abs_z",
                "dominant_window",
                "n_windows_watch",
                "z_w1",
                "z_w3",
                "z_w5",
                "z_w7",
            ]
        )

    meta_cols = ["series_id", "country", "partner", "flow", "metric"]
    rows: list[dict] = []
    for keys, group in scores.groupby(meta_cols + ["year"], sort=False):
        z_by_window = _max_abs_z_by_window(group)
        tier = classify_tier(z_by_window)
        anomaly_type = classify_type(z_by_window, tier)
        dominant_window = (
            max(z_by_window, key=z_by_window.get) if z_by_window else np.nan
        )
        rows.append(
            {
                "series_id": keys[0],
                "country": keys[1],
                "partner": keys[2],
                "flow": keys[3],
                "metric": keys[4],
                "year": int(keys[5]),
                "tier": tier,
                "anomaly_type": anomaly_type,
                "max_abs_z": max(z_by_window.values()) if z_by_window else 0.0,
                "dominant_window": dominant_window,
                "n_windows_watch": sum(
                    1 for z in z_by_window.values() if z >= Z_WATCH
                ),
                "z_w1": z_by_window.get(1, np.nan),
                "z_w3": z_by_window.get(3, np.nan),
                "z_w5": z_by_window.get(5, np.nan),
                "z_w7": z_by_window.get(7, np.nan),
            }
        )

    alerts = pd.DataFrame(rows).sort_values(
        ["country", "partner", "flow", "metric", "year"]
    ).reset_index(drop=True)
    return _apply_persistence_upgrade(alerts)


def _apply_persistence_upgrade(alerts: pd.DataFrame) -> pd.DataFrame:
    """Upgrade Alert to Critical after sustained structural elevation."""
    if alerts.empty:
        return alerts

    result = alerts.copy()
    for _, group in result.groupby("series_id", sort=False):
        group = group.sort_values("year")
        elevated = (
            (group["z_w3"].fillna(0) >= Z_ALERT)
            | (group["z_w5"].fillna(0) >= Z_ALERT)
            | (group["z_w7"].fillna(0) >= Z_ALERT)
        )
        run = 0
        for idx, is_elevated in zip(group.index, elevated):
            run = run + 1 if bool(is_elevated) else 0
            if (
                run >= PERSISTENCE_YEARS
                and result.at[idx, "tier"] == TIER_ALERT
            ):
                result.at[idx, "tier"] = TIER_CRITICAL
                if result.at[idx, "anomaly_type"] in (TYPE_NONE, TYPE_LEVEL_SHOCK):
                    result.at[idx, "anomaly_type"] = TYPE_STRUCTURAL_BREAK
    return result


def summarize_alerts(alerts: pd.DataFrame) -> pd.DataFrame:
    """Counts by country, partner, tier."""
    if alerts.empty:
        return pd.DataFrame(
            columns=["country", "partner", "tier", "n_alerts", "n_series_years"]
        )
    flagged = alerts[alerts["tier"] != TIER_NONE]
    if flagged.empty:
        return pd.DataFrame(
            columns=["country", "partner", "tier", "n_alerts", "n_series_years"]
        )
    return (
        flagged.groupby(["country", "partner", "tier"], as_index=False)
        .agg(n_alerts=("year", "count"), n_series_years=("series_id", "nunique"))
        .sort_values(["country", "partner", "tier"])
        .reset_index(drop=True)
    )
