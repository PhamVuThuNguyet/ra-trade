"""One-step forecasting models: naive, Holt linear, AR(1)."""

from __future__ import annotations

import numpy as np

from trade_anomaly.constants import (
    AR1_MIN_POINTS,
    HOLT_ALPHA_GRID,
    HOLT_BETA_GRID,
    MODEL_AR1,
    MODEL_HOLT,
    MODEL_NAIVE,
)


def forecast_naive(history: np.ndarray) -> float:
    """Last-value forecast; requires at least one observation."""
    if history.size < 1:
        raise ValueError("naive forecast needs at least one history point")
    return float(history[-1])


def _holt_fit_forecast(
    history: np.ndarray,
    alpha: float,
    beta: float,
) -> tuple[float, float]:
    """Return (one-step forecast, in-sample SSE) for fixed Holt params."""
    level = float(history[0])
    trend = float(history[1] - history[0]) if history.size >= 2 else 0.0
    sse = 0.0
    for t in range(1, history.size):
        fitted = level + trend
        err = float(history[t]) - fitted
        sse += err * err
        prev_level = level
        level = alpha * float(history[t]) + (1.0 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1.0 - beta) * trend
    return level + trend, sse


def forecast_holt(history: np.ndarray) -> float:
    """Holt additive level+trend; grid-search alpha/beta on in-sample SSE."""
    if history.size < 2:
        return forecast_naive(history)

    best_forecast = forecast_naive(history)
    best_sse = float("inf")
    for alpha in HOLT_ALPHA_GRID:
        for beta in HOLT_BETA_GRID:
            forecast, sse = _holt_fit_forecast(history, alpha, beta)
            if sse < best_sse:
                best_sse = sse
                best_forecast = forecast
    return float(best_forecast)


def forecast_ar1(history: np.ndarray) -> float:
    """AR(1) with intercept via OLS; falls back to naive if too short/singular."""
    if history.size < AR1_MIN_POINTS:
        return forecast_naive(history)

    y = history[1:].astype(float)
    x = history[:-1].astype(float)
    x_design = np.column_stack([np.ones(len(x)), x])
    try:
        coef, _, rank, _ = np.linalg.lstsq(x_design, y, rcond=None)
    except np.linalg.LinAlgError:
        return forecast_naive(history)
    if rank < 2:
        return forecast_naive(history)
    intercept, phi = float(coef[0]), float(coef[1])
    return intercept + phi * float(history[-1])


def forecast_one_step(history: np.ndarray, model: str) -> float:
    """Dispatch one-step forecast for the named model."""
    values = np.asarray(history, dtype=float)
    if model == MODEL_NAIVE:
        return forecast_naive(values)
    if model == MODEL_HOLT:
        return forecast_holt(values)
    if model == MODEL_AR1:
        return forecast_ar1(values)
    raise ValueError(f"Unknown model: {model}")
