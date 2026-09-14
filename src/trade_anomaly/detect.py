"""Residual scoring and per-scale anomaly detection."""

from __future__ import annotations

import numpy as np
import pandas as pd

from trade_anomaly.constants import (
    MODEL_AR1,
    MODEL_HOLT,
    MODEL_NAIVE,
    NAIVE_SIGMA_LOOKBACK,
    ULTRA_SHORT_WINDOW,
    WINDOWS_YEARS,
)
from trade_anomaly.models import forecast_one_step
from trade_anomaly.windows import iter_window_forecast_points


def robust_scale(residuals: np.ndarray) -> float:
    """MAD-based scale (approx sigma); fallback to sample std / abs mean."""
    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 1.0
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    scale = 1.4826 * mad
    if scale > 1e-12:
        return float(scale)
    std = float(np.std(values, ddof=1)) if values.size >= 2 else 0.0
    if std > 1e-12:
        return std
    mean_abs = float(np.mean(np.abs(values)))
    if mean_abs > 1e-12:
        return mean_abs
    return 1.0


def _models_for_window(window: int) -> tuple[str, ...]:
    if window <= ULTRA_SHORT_WINDOW:
        return (MODEL_NAIVE,)
    return (MODEL_HOLT, MODEL_AR1)


def score_series(
    series: pd.DataFrame,
    *,
    windows: tuple[int, ...] = WINDOWS_YEARS,
    series_id: str | None = None,
) -> pd.DataFrame:
    """
    Compute one-step residual z-scores for each window and model.

    ``series`` must include year, value, and optional metadata columns
    (country, partner, flow, metric, series_id).
    """
    meta = {}
    for col in ("series_id", "country", "partner", "flow", "metric"):
        if col in series.columns and series[col].nunique(dropna=False) == 1:
            meta[col] = series[col].iloc[0]
    if series_id is not None:
        meta["series_id"] = series_id

    rows: list[dict] = []
    ordered = series.sort_values("year").reset_index(drop=True)
    all_years = ordered["year"].to_numpy(dtype=int)
    all_values = ordered["value"].to_numpy(dtype=float)

    for window in windows:
        models = _models_for_window(window)
        # Collect residuals chronologically to build expanding/robust sigma.
        for model in models:
            residual_history: list[float] = []
            for target_year, history, actual in iter_window_forecast_points(
                ordered, window
            ):
                prediction = forecast_one_step(history, model)
                residual = actual - prediction
                # Sigma from prior residuals; bootstrap with history one-step
                # naive errors when buffer is empty.
                if residual_history:
                    scale_src = np.asarray(residual_history, dtype=float)
                else:
                    # Seed sigma from absolute deviations vs last history mean.
                    seed = history - np.mean(history) if history.size > 1 else history
                    if window == ULTRA_SHORT_WINDOW:
                        # Use trailing series values around the cut for scale.
                        idx = int(np.where(all_years == target_year)[0][0])
                        start = max(0, idx - NAIVE_SIGMA_LOOKBACK)
                        local = all_values[start:idx]
                        seed = local - np.mean(local) if local.size else np.array([1.0])
                    scale_src = np.asarray(seed, dtype=float)
                scale = robust_scale(scale_src)
                z = residual / scale
                residual_history.append(residual)
                row = {
                    **meta,
                    "year": target_year,
                    "window": window,
                    "model": model,
                    "actual": actual,
                    "forecast": prediction,
                    "residual": residual,
                    "scale": scale,
                    "z": z,
                    "abs_z": abs(z),
                }
                rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=[
                "series_id",
                "country",
                "partner",
                "flow",
                "metric",
                "year",
                "window",
                "model",
                "actual",
                "forecast",
                "residual",
                "scale",
                "z",
                "abs_z",
            ]
        )
    return pd.DataFrame(rows)


def score_all_series(
    series_panel: pd.DataFrame,
    *,
    windows: tuple[int, ...] = WINDOWS_YEARS,
) -> pd.DataFrame:
    """Score every series_id in a long series panel."""
    if series_panel.empty:
        return score_series(series_panel, windows=windows)

    frames: list[pd.DataFrame] = []
    for series_id, group in series_panel.groupby("series_id", sort=False):
        scored = score_series(group, windows=windows, series_id=str(series_id))
        if not scored.empty:
            frames.append(scored)
    if not frames:
        return score_series(series_panel.iloc[0:0], windows=windows)
    return pd.concat(frames, ignore_index=True)
