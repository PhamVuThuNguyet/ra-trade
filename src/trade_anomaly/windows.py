"""Sliding-window iteration helpers."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd

from trade_anomaly.constants import STRIDE_YEARS, WINDOWS_YEARS


def sorted_series_frame(series: pd.DataFrame) -> pd.DataFrame:
    """Return year-sorted copy with required columns."""
    required = {"year", "value"}
    missing = required - set(series.columns)
    if missing:
        raise KeyError(f"Series missing columns: {sorted(missing)}")
    return series.sort_values("year").reset_index(drop=True)


def iter_window_forecast_points(
    series: pd.DataFrame,
    window: int,
    stride: int = STRIDE_YEARS,
) -> Iterator[tuple[int, np.ndarray, float]]:
    """
    Yield (target_year, history_values, actual_value) for each valid cut.

    History is the ``window`` observations immediately before the target year
    in the observed series (not calendar gaps). Target must exist in series.
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    if stride < 1:
        raise ValueError("stride must be >= 1")

    frame = sorted_series_frame(series)
    years = frame["year"].to_numpy(dtype=int)
    values = frame["value"].to_numpy(dtype=float)
    n = len(frame)
    # First target index is ``window`` (0-based); then step by stride.
    for target_idx in range(window, n, stride):
        history = values[target_idx - window : target_idx]
        yield int(years[target_idx]), history, float(values[target_idx])


def default_windows() -> tuple[int, ...]:
    return WINDOWS_YEARS
