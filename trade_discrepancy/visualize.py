from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from trade_discrepancy.constants import (
    DISCREPANCY_TOLERANCE_PCT,
    FLOW_ORDER,
    IMF_TO_COMTRADE_COUNTRY,
    OUTPUT_PLOTS_DIR,
    PARTNER_ORDER,
    PARTNER_WORLD,
)

FIGURE_DPI = 150
HEATMAP_VMIN = -50
HEATMAP_VMAX = 50
COUNTRY_LABEL_COL = "country_label"
COMTRADE_STYLE = {
    "color": "#1f77b4",
    "linestyle": "-",
    "linewidth": 2,
    "marker": "o",
    "markersize": 4,
}
IMF_STYLE = {
    "color": "#ff7f0e",
    "linestyle": "--",
    "linewidth": 2,
    "marker": "s",
    "markersize": 4,
}


def _save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _with_comtrade_country_labels(frame: pd.DataFrame) -> pd.DataFrame:
    labeled = frame.copy()
    if "country_comtrade" in labeled.columns:
        labeled[COUNTRY_LABEL_COL] = labeled["country_comtrade"]
    elif "country" in labeled.columns:
        labeled[COUNTRY_LABEL_COL] = labeled["country"].map(
            lambda name: IMF_TO_COMTRADE_COUNTRY.get(name, name)
        )
    else:
        raise KeyError("Expected 'country_comtrade' or 'country' for plot labels")
    return labeled


def plot_scatter_comparison(
    metrics: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR
) -> Path:
    """IMF vs Comtrade scatter with a 45-degree reference line."""
    fig, ax = plt.subplots(figsize=(8, 8))
    subset = metrics[metrics["partner"] == PARTNER_WORLD]
    ax.scatter(
        subset["comtrade_value_musd"],
        subset["imf_value_musd"],
        alpha=0.7,
        edgecolors="k",
        linewidths=0.3,
    )
    max_val = max(subset["comtrade_value_musd"].max(), subset["imf_value_musd"].max())
    ax.plot([0, max_val], [0, max_val], "r--", linewidth=1, label="Perfect agreement")
    ax.set_xlabel("Comtrade (millions USD)")
    ax.set_ylabel("IMF (millions USD)")
    ax.set_title("World trade totals: IMF vs Comtrade")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save_figure(fig, output_dir, "scatter_world_totals.png")


def _plot_layered_values_on_axis(
    ax: plt.Axes,
    group: pd.DataFrame,
    *,
    title: str,
    show_legend: bool = False,
) -> None:
    ordered = group.sort_values("year")
    ax.plot(
        ordered["year"],
        ordered["comtrade_value_musd"],
        label="Comtrade",
        **COMTRADE_STYLE,
    )
    ax.plot(
        ordered["year"],
        ordered["imf_value_musd"],
        label="IMF",
        **IMF_STYLE,
    )
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Trade value (millions USD)")
    ax.grid(True, alpha=0.3)
    if show_legend:
        ax.legend(loc="best", fontsize=8)


def plot_layered_value_timeseries_by_partner(
    metrics: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR
) -> list[Path]:
    """Overview grid: countries as rows, flows as columns, IMF + Comtrade overlaid."""
    paths: list[Path] = []
    labeled = _with_comtrade_country_labels(metrics)
    for partner in PARTNER_ORDER:
        partner_data = labeled[labeled["partner"] == partner]
        if partner_data.empty:
            continue
        countries = sorted(partner_data[COUNTRY_LABEL_COL].unique())
        fig, axes = plt.subplots(
            len(countries),
            len(FLOW_ORDER),
            figsize=(5 * len(FLOW_ORDER), 2.8 * len(countries)),
            sharex="col",
            squeeze=False,
        )
        for row_idx, country in enumerate(countries):
            country_data = partner_data[partner_data[COUNTRY_LABEL_COL] == country]
            for col_idx, flow in enumerate(FLOW_ORDER):
                ax = axes[row_idx, col_idx]
                panel = country_data[country_data["flow"] == flow]
                if panel.empty:
                    ax.set_visible(False)
                    continue
                _plot_layered_values_on_axis(
                    ax,
                    panel,
                    title=f"{country} — {flow.title()}",
                    show_legend=(row_idx == 0 and col_idx == len(FLOW_ORDER) - 1),
                )
        fig.suptitle(
            f"Layered trade values by country ({partner.upper()})", y=1.01, fontsize=12
        )
        fig.tight_layout()
        paths.append(
            _save_figure(fig, output_dir, f"layered_values_overview_{partner}.png")
        )
    return paths


def plot_discrepancy_timeseries(
    metrics: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR
) -> list[Path]:
    """Symmetric % difference over time, faceted by flow and partner."""
    paths: list[Path] = []
    labeled = _with_comtrade_country_labels(metrics)
    for partner in PARTNER_ORDER:
        subset = labeled[labeled["partner"] == partner]
        if subset.empty:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
        for ax, flow in zip(axes, FLOW_ORDER):
            flow_data = subset[subset["flow"] == flow]
            for country, group in flow_data.groupby(COUNTRY_LABEL_COL):
                ax.plot(
                    group["year"],
                    group["symmetric_pct_diff"],
                    marker="o",
                    label=country,
                    linewidth=1,
                )
            ax.axhline(0, color="black", linewidth=0.8)
            ax.axhline(DISCREPANCY_TOLERANCE_PCT, color="gray", linestyle="--", linewidth=0.8)
            ax.axhline(-DISCREPANCY_TOLERANCE_PCT, color="gray", linestyle="--", linewidth=0.8)
            ax.set_title(f"{flow.title()} — {partner.upper()}")
            ax.set_xlabel("Year")
            ax.set_ylabel("Symmetric % difference")
            ax.grid(True, alpha=0.3)
        handles, labels = axes[0].get_legend_handles_labels()
        if handles:
            fig.legend(
                handles,
                labels,
                loc="upper center",
                ncol=3,
                fontsize=8,
                bbox_to_anchor=(0.5, 1.12),
            )
        fig.suptitle(f"Temporal discrepancies ({partner})", y=1.02)
        fig.tight_layout()
        paths.append(_save_figure(fig, output_dir, f"timeseries_{partner}.png"))
    return paths


def plot_discrepancy_heatmap(
    summary: pd.DataFrame, output_dir: Path = OUTPUT_PLOTS_DIR
) -> Path:
    """Heatmap of median symmetric % difference by country, flow, and partner."""
    labeled = _with_comtrade_country_labels(summary)
    pivot_data = labeled.pivot_table(
        index=COUNTRY_LABEL_COL,
        columns=["flow", "partner"],
        values="median_symmetric_pct_diff",
    )
    fig, ax = plt.subplots(figsize=(10, max(4, 0.4 * len(pivot_data))))
    image = ax.imshow(
        pivot_data.values,
        aspect="auto",
        cmap="RdBu_r",
        vmin=HEATMAP_VMIN,
        vmax=HEATMAP_VMAX,
    )
    ax.set_xticks(range(len(pivot_data.columns)))
    ax.set_xticklabels(
        [f"{flow}/{partner}" for flow, partner in pivot_data.columns],
        rotation=45,
        ha="right",
    )
    ax.set_yticks(range(len(pivot_data.index)))
    ax.set_yticklabels(pivot_data.index)
    ax.set_title("Median symmetric % difference (IMF vs Comtrade)")
    fig.colorbar(image, ax=ax, label="% difference")
    fig.tight_layout()
    return _save_figure(fig, output_dir, "heatmap_median_discrepancy.png")


def generate_all_plots(
    metrics: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> list[Path]:
    """Write plots that tables cannot show: scatter, heatmap, overlays, and % trends."""
    if output_dir.exists():
        for stale in output_dir.glob("*.png"):
            stale.unlink()

    paths = [
        plot_scatter_comparison(metrics, output_dir),
        plot_discrepancy_heatmap(summary, output_dir),
    ]
    paths.extend(plot_layered_value_timeseries_by_partner(metrics, output_dir))
    paths.extend(plot_discrepancy_timeseries(metrics, output_dir))
    return paths
