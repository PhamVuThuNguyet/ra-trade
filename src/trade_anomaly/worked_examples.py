"""Manuscript worked-example figures for multi-scale anomaly findings."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from trade_anomaly.constants import (
    OUTPUT_PLOTS_DIR,
    PARTNER_PLOT_COLORS,
    TIER_ALERT,
    TIER_CRITICAL,
    TIER_WATCH,
    WINDOWS_YEARS,
    WORKED_EXAMPLES,
    Z_ALERT,
    Z_CRITICAL,
    Z_DISPLAY_CAP,
    Z_WATCH,
)

TIER_COLORS = {
    TIER_WATCH: "#ffcc66",
    TIER_ALERT: "#ff7f0e",
    TIER_CRITICAL: "#d62728",
}

_Z_COLS = {1: "z_w1", 3: "z_w3", 5: "z_w5", 7: "z_w7"}


def _save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _max_z_by_window(alerts_row: pd.Series) -> dict[int, float]:
    out: dict[int, float] = {}
    for window, col in _Z_COLS.items():
        if col in alerts_row.index and pd.notna(alerts_row[col]):
            out[window] = float(alerts_row[col])
    return out


def _plot_series_panel(
    ax: plt.Axes,
    series: pd.DataFrame,
    alerts: pd.DataFrame,
    *,
    focus_years: tuple[int, ...],
    ylabel: str,
    value_scale: float,
) -> None:
    partner = series["partner"].iloc[0]
    years = series["year"].to_numpy(dtype=int)
    values = series["value"].to_numpy(dtype=float) / value_scale
    ax.plot(
        years,
        values,
        marker="o",
        linewidth=2.2,
        color=PARTNER_PLOT_COLORS.get(partner, "#333333"),
        label="Observed",
    )

    series_alerts = alerts[alerts["series_id"] == series["series_id"].iloc[0]]
    for _, row in series_alerts.iterrows():
        if row["tier"] not in TIER_COLORS:
            continue
        ax.axvline(
            int(row["year"]),
            color=TIER_COLORS[row["tier"]],
            alpha=0.28,
            linewidth=5,
            zorder=0,
        )

    for year in focus_years:
        focus = series_alerts[series_alerts["year"] == year]
        if focus.empty:
            continue
        tier = focus.iloc[0]["tier"]
        y_val = float(series.loc[series["year"] == year, "value"].iloc[0]) / value_scale
        ax.scatter(
            [year],
            [y_val],
            s=90,
            zorder=5,
            color=TIER_COLORS.get(tier, "#333333"),
            edgecolors="black",
            linewidths=0.8,
            label=f"{year}: {tier}",
        )

    ax.set_ylabel(ylabel)
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)


def _plot_z_panel(
    ax: plt.Axes,
    alerts: pd.DataFrame,
    series_id: str,
    focus_years: tuple[int, ...],
) -> None:
    windows = list(WINDOWS_YEARS)
    n_years = len(focus_years)
    width = 0.8 / max(n_years, 1)
    x = np.arange(len(windows))

    for i, year in enumerate(focus_years):
        row = alerts[(alerts["series_id"] == series_id) & (alerts["year"] == year)]
        if row.empty:
            zs = [np.nan] * len(windows)
        else:
            zmap = _max_z_by_window(row.iloc[0])
            zs = [zmap.get(w, np.nan) for w in windows]
        display = [
            min(z, Z_DISPLAY_CAP) if np.isfinite(z) else np.nan for z in zs
        ]
        offset = (i - (n_years - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            display,
            width=width * 0.9,
            label=str(year),
            alpha=0.85,
        )
        for bar, raw in zip(bars, zs):
            if np.isfinite(raw) and raw > Z_DISPLAY_CAP:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    Z_DISPLAY_CAP * 0.97,
                    f"{raw:.0f}",
                    ha="center",
                    va="top",
                    fontsize=7,
                    rotation=90,
                )

    for thresh, style, name in (
        (Z_WATCH, ":", "Watch"),
        (Z_ALERT, "--", "Alert"),
        (Z_CRITICAL, "-", "Critical"),
    ):
        ax.axhline(thresh, color="grey", linestyle=style, linewidth=1, alpha=0.8)
        ax.text(
            len(windows) - 0.45,
            thresh + 0.15,
            name,
            fontsize=7,
            color="grey",
            ha="right",
        )

    ax.set_xticks(x)
    ax.set_xticklabels([f"w={w}" for w in windows])
    ax.set_ylabel(f"Max |z| (capped at {Z_DISPLAY_CAP:g})")
    ax.set_xlabel("Window (years)")
    ax.set_ylim(0, Z_DISPLAY_CAP * 1.08)
    ax.grid(True, axis="y", alpha=0.3)
    if n_years > 1:
        ax.legend(title="Focus year", fontsize=8)


def plot_worked_example(
    series_panel: pd.DataFrame,
    alerts: pd.DataFrame,
    example: dict,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> Path | None:
    """Two-panel figure: series path + multi-scale |z| for focus years."""
    series_id = example["series_id"]
    series = series_panel[series_panel["series_id"] == series_id].sort_values("year")
    if series.empty:
        return None

    fig, (ax_series, ax_z) = plt.subplots(
        2,
        1,
        figsize=(9.5, 6.5),
        gridspec_kw={"height_ratios": [1.35, 1.0]},
    )
    _plot_series_panel(
        ax_series,
        series,
        alerts,
        focus_years=tuple(example["focus_years"]),
        ylabel=example["ylabel"],
        value_scale=float(example["value_scale"]),
    )
    ax_series.set_title(example["title"], fontsize=11)
    _plot_z_panel(ax_z, alerts, series_id, tuple(example["focus_years"]))
    fig.tight_layout()
    return _save_figure(fig, output_dir, example["filename"])


def plot_worked_examples_overview(
    series_panel: pd.DataFrame,
    alerts: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> Path:
    """2×2 overview of all manuscript worked examples (series panels only)."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), squeeze=False)
    for ax, example in zip(axes.ravel(), WORKED_EXAMPLES):
        series_id = example["series_id"]
        series = series_panel[series_panel["series_id"] == series_id].sort_values(
            "year"
        )
        if series.empty:
            ax.set_title(f"Missing: {series_id}", fontsize=9)
            ax.axis("off")
            continue
        _plot_series_panel(
            ax,
            series,
            alerts,
            focus_years=tuple(example["focus_years"]),
            ylabel=example["ylabel"],
            value_scale=float(example["value_scale"]),
        )
        ax.set_title(example["title"], fontsize=9)
    fig.suptitle("Worked example findings (manuscript §8)", fontsize=12, y=1.01)
    fig.tight_layout()
    return _save_figure(fig, output_dir, "example_worked_findings_overview.png")


def generate_worked_example_plots(
    series_panel: pd.DataFrame,
    alerts: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> list[Path]:
    """Write individual worked-example figures plus a 2×2 overview."""
    paths: list[Path] = []
    for example in WORKED_EXAMPLES:
        path = plot_worked_example(series_panel, alerts, example, output_dir)
        if path is not None:
            paths.append(path)
    paths.append(plot_worked_examples_overview(series_panel, alerts, output_dir))
    return paths
