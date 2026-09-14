"""ACF diagnostics to inform window-size choices."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sample_acf(values: np.ndarray, max_lag: int | None = None) -> pd.DataFrame:
    """
    Sample autocorrelation r_k for lags 1..max_lag.

    Uses the standard mean-centered formula from the study design.
    """
    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = y.size
    if n < 3:
        return pd.DataFrame(columns=["lag", "acf"])

    if max_lag is None:
        max_lag = max(1, min(n // 2, 10))
    max_lag = int(min(max_lag, n - 1))

    mean = float(np.mean(y))
    denom = float(np.sum((y - mean) ** 2))
    if denom <= 0:
        return pd.DataFrame({"lag": list(range(1, max_lag + 1)), "acf": [0.0] * max_lag})

    rows = []
    for lag in range(1, max_lag + 1):
        num = float(np.sum((y[lag:] - mean) * (y[:-lag] - mean)))
        rows.append({"lag": lag, "acf": num / denom})
    return pd.DataFrame(rows)


def suggest_min_window(acf: pd.DataFrame, bound: float | None = None) -> int | None:
    """
    Suggest a minimum window as the largest lag with |acf| above a bound.

    Default bound approximates 1.96/sqrt(n) when n is encoded via acf length;
    callers may pass an explicit bound.
    """
    if acf.empty:
        return None
    if bound is None:
        # Conservative default when n unknown: 0.3
        bound = 0.3
    significant = acf[acf["acf"].abs() >= bound]
    if significant.empty:
        return 1
    return int(significant["lag"].max())


def acf_summary_for_panel(
    series_panel: pd.DataFrame,
    *,
    max_lag: int = 7,
) -> pd.DataFrame:
    """Per-series ACF peak lag and suggested minimum window."""
    rows: list[dict] = []
    for series_id, group in series_panel.groupby("series_id", sort=False):
        values = group.sort_values("year")["value"].to_numpy(dtype=float)
        acf = sample_acf(values, max_lag=max_lag)
        n = int(np.isfinite(values).sum())
        bound = 1.96 / np.sqrt(n) if n > 0 else 0.3
        peak = acf.loc[acf["acf"].abs().idxmax()] if not acf.empty else None
        rows.append(
            {
                "series_id": series_id,
                "country": group["country"].iloc[0],
                "partner": group["partner"].iloc[0],
                "flow": group["flow"].iloc[0],
                "metric": group["metric"].iloc[0],
                "n_obs": n,
                "acf_bound": bound,
                "peak_lag": int(peak["lag"]) if peak is not None else np.nan,
                "peak_acf": float(peak["acf"]) if peak is not None else np.nan,
                "suggested_min_window": suggest_min_window(acf, bound=bound),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "series_id",
                "country",
                "partner",
                "flow",
                "metric",
                "n_obs",
                "acf_bound",
                "peak_lag",
                "peak_acf",
                "suggested_min_window",
            ]
        )
    return pd.DataFrame(rows)
