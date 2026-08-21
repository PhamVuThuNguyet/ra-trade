"""Time-series drawing helpers for trade influence indices."""

from math import ceil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

from trade_influence.constants import (
    BILATERAL_PARTNERS,
    INDEX_DISPLAY,
    OUTPUT_PLOTS_DIR,
    PARTNER_DISPLAY,
    PARTNER_PLOT_COLORS,
    SOURCE_COMTRADE,
    SOURCE_IMF,
    SOURCE_LINESTYLES,
    display_country,
)


def _save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _axis_label(value_col: str) -> str:
    return INDEX_DISPLAY.get(value_col, value_col)


def _grid_shape(n_panels: int) -> tuple[int, int]:
    if n_panels <= 3:
        return n_panels, 1
    ncols = 2 if n_panels <= 8 else 3
    return ceil(n_panels / ncols), ncols


def _country_color_map(countries: list[str]) -> dict[str, tuple]:
    cmap = plt.get_cmap("tab10")
    return {country: cmap(i % 10) for i, country in enumerate(countries)}


def _style_share_axis(ax: plt.Axes, ylabel: str | None = None) -> None:
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    if ylabel:
        ax.set_ylabel(ylabel)


def _plot_partner_lines(
    ax: plt.Axes,
    frame: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    *,
    linestyle: str = "-",
    label_suffix: str = "",
) -> None:
    for partner in partners:
        series = frame[frame["partner"] == partner].sort_values("year")
        if series.empty or series[value_col].isna().all():
            continue
        ax.plot(
            series["year"],
            series[value_col],
            marker="o",
            markersize=3.5,
            linewidth=2,
            linestyle=linestyle,
            color=PARTNER_PLOT_COLORS.get(partner, None),
            label=PARTNER_DISPLAY.get(partner, partner) + label_suffix,
        )


def plot_index_timeseries_by_country(
    indices: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title: str,
    filename: str,
) -> Path:
    """Country grid; partner lines over years; one shared legend."""
    countries = sorted(indices["country"].unique())
    nrows, ncols = _grid_shape(len(countries) or 1)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(6.4 * ncols, 2.7 * nrows), sharex=True, squeeze=False
    )
    label = _axis_label(value_col)
    legend_handles = legend_labels = None
    for i, country in enumerate(countries):
        ax = axes[i // ncols, i % ncols]
        _plot_partner_lines(
            ax, indices[indices["country"] == country], value_col, partners
        )
        ax.set_title(display_country(country))
        _style_share_axis(ax, ylabel=label if i % ncols == 0 else None)
        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()
    for ax in axes.flat[len(countries) :]:
        ax.set_visible(False)
    for ax in axes[-1, :]:
        if ax.get_visible():
            ax.set_xlabel("Year")
    if legend_handles:
        fig.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            ncol=max(len(partners), 1),
            fontsize=9,
            bbox_to_anchor=(0.5, 1.02),
        )
    fig.suptitle(title, y=1.06, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, filename)


def plot_index_timeseries_by_partner(
    indices: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title_prefix: str,
    filename_prefix: str,
) -> list[Path]:
    """One figure per partner; country lines over years."""
    paths: list[Path] = []
    label = _axis_label(value_col)
    for partner in partners:
        subset = indices[indices["partner"] == partner]
        if subset.empty or subset[value_col].isna().all():
            continue
        countries = sorted(subset["country"].unique())
        colors = _country_color_map(countries)
        fig, ax = plt.subplots(figsize=(10, 5.2))
        for country in countries:
            series = subset[subset["country"] == country].sort_values("year")
            ax.plot(
                series["year"],
                series[value_col],
                marker="o",
                markersize=3.5,
                linewidth=1.8,
                color=colors[country],
                label=display_country(country),
            )
        ax.set_xlabel("Year")
        _style_share_axis(ax, ylabel=label)
        ax.set_title(f"{title_prefix} — {PARTNER_DISPLAY.get(partner, partner)}")
        ax.legend(loc="best", fontsize=8, ncol=2)
        fig.tight_layout()
        paths.append(_save_figure(fig, output_dir, f"{filename_prefix}_{partner}.png"))
    return paths


def plot_comtrade_vs_imf_timeseries(
    indices_comtrade: pd.DataFrame,
    indices_imf: pd.DataFrame,
    value_col: str,
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title: str,
    filename: str,
) -> Path:
    """Country grid overlay: solid Comtrade, dashed IMF."""
    shared = sorted(
        set(indices_comtrade["country"].unique()) & set(indices_imf["country"].unique())
    )
    if not shared:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No overlapping countries", ha="center", va="center")
        ax.axis("off")
        return _save_figure(fig, output_dir, filename)

    nrows, ncols = _grid_shape(len(shared))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(6.4 * ncols, 2.8 * nrows), sharex=True, squeeze=False
    )
    label = _axis_label(value_col)
    legend_handles = legend_labels = None
    for i, country in enumerate(shared):
        ax = axes[i // ncols, i % ncols]
        _plot_partner_lines(
            ax,
            indices_comtrade[indices_comtrade["country"] == country],
            value_col,
            BILATERAL_PARTNERS,
            linestyle=SOURCE_LINESTYLES[SOURCE_COMTRADE],
            label_suffix=" (Comtrade)",
        )
        _plot_partner_lines(
            ax,
            indices_imf[indices_imf["country"] == country],
            value_col,
            BILATERAL_PARTNERS,
            linestyle=SOURCE_LINESTYLES[SOURCE_IMF],
            label_suffix=" (IMF)",
        )
        ax.set_title(display_country(country))
        _style_share_axis(ax, ylabel=label if i % ncols == 0 else None)
        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()
    for ax in axes.flat[len(shared) :]:
        ax.set_visible(False)
    for ax in axes[-1, :]:
        if ax.get_visible():
            ax.set_xlabel("Year")
    if legend_handles:
        fig.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            ncol=3,
            fontsize=8,
            bbox_to_anchor=(0.5, 1.02),
        )
    fig.suptitle(title, y=1.07, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, filename)


def plot_comtrade_vs_imf_by_partner(
    indices_comtrade: pd.DataFrame,
    indices_imf: pd.DataFrame,
    value_col: str,
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title_prefix: str,
    filename_prefix: str,
) -> list[Path]:
    """One overlay per partner: country colour, solid Comtrade / dashed IMF."""
    shared = sorted(
        set(indices_comtrade["country"].unique()) & set(indices_imf["country"].unique())
    )
    if not shared:
        return []
    colors = _country_color_map(shared)
    label = _axis_label(value_col)
    paths: list[Path] = []
    for partner in BILATERAL_PARTNERS:
        fig, ax = plt.subplots(figsize=(10, 5.2))
        for country in shared:
            color = colors[country]
            name = display_country(country)
            for frame, linestyle in (
                (indices_comtrade, SOURCE_LINESTYLES[SOURCE_COMTRADE]),
                (indices_imf, SOURCE_LINESTYLES[SOURCE_IMF]),
            ):
                series = frame[
                    (frame["country"] == country) & (frame["partner"] == partner)
                ].sort_values("year")
                if series.empty or series[value_col].isna().all():
                    continue
                ax.plot(
                    series["year"],
                    series[value_col],
                    marker="o",
                    markersize=3.5,
                    linewidth=1.8,
                    linestyle=linestyle,
                    color=color,
                    label=(
                        name
                        if linestyle == SOURCE_LINESTYLES[SOURCE_COMTRADE]
                        else "_nolegend_"
                    ),
                )
        ax.set_xlabel("Year")
        _style_share_axis(ax, ylabel=label)
        ax.set_title(
            f"{title_prefix} — {PARTNER_DISPLAY[partner]} "
            "(solid Comtrade, dashed IMF)"
        )
        country_handles, country_labels = ax.get_legend_handles_labels()
        style_handles = [
            Line2D([0], [0], color="0.25", linestyle="-", label="Comtrade"),
            Line2D([0], [0], color="0.25", linestyle="--", label="IMF"),
        ]
        ax.legend(
            country_handles + style_handles,
            country_labels + ["Comtrade", "IMF"],
            loc="best",
            fontsize=8,
            ncol=2,
        )
        fig.tight_layout()
        paths.append(_save_figure(fig, output_dir, f"{filename_prefix}_{partner}.png"))
    return paths
