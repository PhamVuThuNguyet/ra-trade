"""Plots for multi-scale trade anomaly alerts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from trade_anomaly.constants import (
    OUTPUT_PLOTS_DIR,
    PARTNER_DISPLAY,
    PARTNER_PLOT_COLORS,
    TIER_ALERT,
    TIER_CRITICAL,
    TIER_WATCH,
)

TIER_COLORS = {
    TIER_WATCH: "#ffcc66",
    TIER_ALERT: "#ff7f0e",
    TIER_CRITICAL: "#d62728",
}


def _save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_tier_counts(alerts: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR) -> Path:
    """Bar chart of alert counts by tier."""
    flagged = alerts[alerts["tier"].isin(TIER_COLORS)]
    counts = (
        flagged["tier"].value_counts().reindex(list(TIER_COLORS), fill_value=0)
        if not flagged.empty
        else pd.Series({t: 0 for t in TIER_COLORS})
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        list(counts.index),
        counts.values,
        color=[TIER_COLORS[t] for t in counts.index],
    )
    ax.set_title("Attention flags by severity tier")
    ax.set_ylabel("Series–year counts")
    ax.set_xlabel("Tier")
    return _save_figure(fig, output_dir, "tier_counts.png")


def plot_alerts_by_partner(
    alerts: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR
) -> Path:
    """Stacked bars: partner × tier."""
    flagged = alerts[alerts["tier"].isin(TIER_COLORS)]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if flagged.empty:
        ax.set_title("Alerts by partner (none)")
        return _save_figure(fig, output_dir, "alerts_by_partner.png")

    pivot = (
        flagged.groupby(["partner", "tier"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=list(TIER_COLORS), fill_value=0)
    )
    partners = list(pivot.index)
    x = np.arange(len(partners))
    bottom = np.zeros(len(partners))
    for tier in TIER_COLORS:
        vals = pivot[tier].to_numpy(dtype=float)
        ax.bar(
            x,
            vals,
            bottom=bottom,
            color=TIER_COLORS[tier],
            label=tier,
        )
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels([PARTNER_DISPLAY.get(p, p) for p in partners])
    ax.set_ylabel("Series–year counts")
    ax.set_title("Attention flags by partner and tier")
    ax.legend()
    return _save_figure(fig, output_dir, "alerts_by_partner.png")


def plot_example_series_with_alerts(
    series_panel: pd.DataFrame,
    alerts: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    n_examples: int = 6,
) -> Path:
    """Plot top flagged series with tier markers."""
    flagged = alerts[alerts["tier"].isin(TIER_COLORS)].copy()
    fig, axes = plt.subplots(
        n_examples,
        1,
        figsize=(10, max(2.0 * n_examples, 4)),
        sharex=False,
        squeeze=False,
    )

    if flagged.empty:
        axes[0, 0].set_title("No flagged series")
        return _save_figure(fig, output_dir, "example_series_alerts.png")

    severity = {TIER_CRITICAL: 3, TIER_ALERT: 2, TIER_WATCH: 1}
    flagged["sev"] = flagged["tier"].map(severity)
    top_ids = (
        flagged.groupby("series_id")["sev"]
        .max()
        .sort_values(ascending=False)
        .head(n_examples)
        .index.tolist()
    )

    for ax, series_id in zip(axes[:, 0], top_ids):
        series = series_panel[series_panel["series_id"] == series_id].sort_values(
            "year"
        )
        series_alerts = flagged[flagged["series_id"] == series_id]
        partner = series["partner"].iloc[0]
        ax.plot(
            series["year"],
            series["value"],
            marker="o",
            color=PARTNER_PLOT_COLORS.get(partner, "#333333"),
            linewidth=2,
        )
        for _, row in series_alerts.iterrows():
            ax.axvline(
                row["year"],
                color=TIER_COLORS[row["tier"]],
                alpha=0.35,
                linewidth=4,
            )
        ax.set_title(str(series_id), fontsize=9)
        ax.grid(True, alpha=0.25)

    for ax in axes[len(top_ids) :, 0]:
        ax.axis("off")

    fig.suptitle("Example series with attention flags", y=1.01)
    fig.tight_layout()
    return _save_figure(fig, output_dir, "example_series_alerts.png")


def plot_multiscale_z_heatmap(
    scores: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    max_series: int = 20,
) -> Path:
    """Heatmap of max |z| by series and window for top series."""
    if scores.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.set_title("Multi-scale |z| (empty)")
        return _save_figure(fig, output_dir, "multiscale_z_heatmap.png")

    pivot = (
        scores.groupby(["series_id", "window"])["abs_z"]
        .max()
        .unstack(fill_value=0.0)
        .sort_index(axis=1)
    )
    rank = pivot.max(axis=1).sort_values(ascending=False).head(max_series)
    pivot = pivot.loc[rank.index]

    fig, ax = plt.subplots(figsize=(10, max(0.35 * len(pivot), 4)))
    im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"w={c}" for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.set_title("Multi-scale max |z| (top series)")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    fig.tight_layout()
    return _save_figure(fig, output_dir, "multiscale_z_heatmap.png")


def generate_all_plots(
    series_panel: pd.DataFrame,
    scores: pd.DataFrame,
    alerts: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> list[Path]:
    """Write the standard anomaly plot set, including manuscript worked examples."""
    from trade_anomaly.worked_examples import generate_worked_example_plots

    paths = [
        plot_tier_counts(alerts, output_dir),
        plot_alerts_by_partner(alerts, output_dir),
        plot_example_series_with_alerts(series_panel, alerts, output_dir),
        plot_multiscale_z_heatmap(scores, output_dir),
    ]
    paths.extend(generate_worked_example_plots(series_panel, alerts, output_dir))
    return paths
