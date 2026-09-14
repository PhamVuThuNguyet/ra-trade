"""BACI index time series with calendar lines and EM-DAT disaster bands."""

from pathlib import Path

import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from event_context.constants import ALL_COUNTRIES, BACI_YEAR_MAX, BACI_YEAR_MIN
from trade_influence.constants import (
    BILATERAL_PARTNERS,
    INDEX_CWE,
    INDEX_CWI,
    INDEX_EXPORT,
    INDEX_IMPORT,
    display_country,
)
from trade_influence.plotting import (
    _axis_label,
    _grid_shape,
    _plot_partner_lines,
    _save_figure,
    _style_share_axis,
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DISASTER_FACE = "#f4d35e"
SPAN_FACE = "#b0b0b0"
CALENDAR_LINE = "0.25"
SPAN_TYPES = frozenset({"covid", "gfc", "ramsi"})
TYPE_SHORT_LABEL = {
    "gfc": "GFC",
    "covid": "COVID",
    "step_up": "Step-up",
    "pacer_plus": "PACER+",
    "ramsi": "RAMSI",
    "security_pact": "Security pact",
    "coup": "Coup",
    "unrest": "Unrest",
    "sanctions": "Sanctions",
    "processing_centre": "RPC",
    "compact_renewal": "COFA",
    "wto_accession": "WTO",
}
LABEL_MAX_CHARS = 22
WORKED_COUNTRIES = (
    "Solomon Islands",
    "Fiji",
    "Tonga",
    "Vanuatu",
)
PLOT_SPECS = (
    (INDEX_IMPORT, "Import index I with events (BACI)", "timeseries_import_index_events"),
    (INDEX_EXPORT, "Export index E with events (BACI)", "timeseries_export_index_events"),
    (INDEX_CWI, "CWI with events (BACI)", "timeseries_cwi_events"),
    (INDEX_CWE, "CWE with events (BACI)", "timeseries_cwe_events"),
)


def _applies_to_country(calendar: pd.DataFrame, country: str) -> pd.DataFrame:
    return calendar[calendar["country"].isin((country, ALL_COUNTRIES))]


def disaster_years(disasters: pd.DataFrame, country: str) -> list[int]:
    """EM-DAT years recorded for one PIC."""
    if disasters is None or disasters.empty:
        return []
    frame = disasters[disasters["country"] == country]
    if "emdat_has_disaster" in frame.columns:
        frame = frame[frame["emdat_has_disaster"] > 0]
    elif "emdat_n_events" in frame.columns:
        frame = frame[frame["emdat_n_events"] > 0]
    years = sorted({int(year) for year in frame["year"]})
    return [year for year in years if BACI_YEAR_MIN <= year <= BACI_YEAR_MAX]


def _draw_disaster_bands(ax: plt.Axes, years: list[int]) -> None:
    for year in years:
        ax.axvspan(year - 0.45, year + 0.45, color=DISASTER_FACE, alpha=0.28, zorder=0)


def event_label(event, *, max_chars: int = LABEL_MAX_CHARS) -> str:
    """Compact name for plot annotations."""
    mapped = TYPE_SHORT_LABEL.get(str(event.event_type))
    if mapped:
        return mapped
    title = str(event.title).strip()
    if len(title) <= max_chars:
        return title
    return title[: max_chars - 1] + "…"


def _draw_calendar_marks(ax: plt.Axes, events: pd.DataFrame) -> None:
    for event in events.itertuples(index=False):
        start = max(int(event.year_start), BACI_YEAR_MIN)
        end = min(int(event.year_end), BACI_YEAR_MAX)
        if end < start:
            continue
        if event.event_type in SPAN_TYPES and end > start:
            ax.axvspan(start - 0.45, end + 0.45, color=SPAN_FACE, alpha=0.18, zorder=0)
        else:
            ax.axvline(start, color=CALENDAR_LINE, linestyle="--", linewidth=0.9, zorder=1)


def _annotate_event_names(
    ax: plt.Axes,
    events: pd.DataFrame,
    *,
    skip_regional: bool = False,
    fontsize: float = 6,
    use_short: bool = True,
) -> None:
    """One rotated label per onset year. Country-specific point events win."""
    frame = events
    if skip_regional and "country" in frame.columns:
        frame = frame[frame["country"] != ALL_COUNTRIES]
    if frame.empty:
        return
    ranked = frame.assign(
        _point=(frame["year_end"] <= frame["year_start"]).astype(int)
    ).sort_values(["year_start", "_point"], ascending=[True, False])
    ymax = ax.get_ylim()[1]
    labelled: set[int] = set()
    for event in ranked.itertuples(index=False):
        year = int(event.year_start)
        if year in labelled or year < BACI_YEAR_MIN or year > BACI_YEAR_MAX:
            continue
        labelled.add(year)
        name = event_label(event) if use_short else str(event.title)
        ax.text(
            year,
            ymax * 0.94,
            name,
            rotation=90,
            va="top",
            ha="right",
            fontsize=fontsize,
            color="0.2",
            zorder=3,
        )


def _overlay_legend_handles() -> list:
    return [
        Patch(facecolor=DISASTER_FACE, alpha=0.28, label="EM-DAT disaster year"),
        Patch(facecolor=SPAN_FACE, alpha=0.18, label="COVID / GFC / RAMSI window"),
        Line2D([0], [0], color=CALENDAR_LINE, linestyle="--", label="Calendar event"),
    ]


def plot_index_with_events(
    indices: pd.DataFrame,
    calendar: pd.DataFrame,
    disasters: pd.DataFrame,
    value_col: str,
    output_dir: Path,
    *,
    title: str,
    filename: str,
) -> Path:
    """Country grid of partner index lines with event marks."""
    countries = sorted(indices["country"].unique())
    nrows, ncols = _grid_shape(len(countries) or 1)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(6.8 * ncols, 3.15 * nrows), sharex=True, squeeze=False
    )
    label = _axis_label(value_col)
    legend_handles = legend_labels = None
    for i, country in enumerate(countries):
        ax = axes[i // ncols, i % ncols]
        events = _applies_to_country(calendar, country)
        _draw_disaster_bands(ax, disaster_years(disasters, country))
        _draw_calendar_marks(ax, events)
        _plot_partner_lines(
            ax, indices[indices["country"] == country], value_col, BILATERAL_PARTNERS
        )
        _annotate_event_names(ax, events, skip_regional=True, fontsize=5.5)
        ax.set_title(display_country(country))
        _style_share_axis(ax, ylabel=label if i % ncols == 0 else None)
        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()
    for ax in axes.flat[len(countries) :]:
        ax.set_visible(False)
    for ax in axes[-1, :]:
        if ax.get_visible():
            ax.set_xlabel("Year")
    extra = _overlay_legend_handles()
    fig.legend(
        (legend_handles or []) + extra,
        (legend_labels or []) + [handle.get_label() for handle in extra],
        loc="upper center",
        ncol=3,
        fontsize=8,
        bbox_to_anchor=(0.5, 1.03),
    )
    fig.suptitle(title, y=1.08, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, filename)


def plot_worked_examples(
    indices: pd.DataFrame,
    calendar: pd.DataFrame,
    disasters: pd.DataFrame,
    output_dir: Path,
) -> Path:
    """Four narrative PICs, import index, with event labels at onset years."""
    countries = [name for name in WORKED_COUNTRIES if name in set(indices["country"])]
    if not countries:
        countries = sorted(indices["country"].unique())[:4]
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.2), sharex=True, squeeze=False)
    for i, country in enumerate(countries[:4]):
        ax = axes[i // 2, i % 2]
        events = _applies_to_country(calendar, country)
        _draw_disaster_bands(ax, disaster_years(disasters, country))
        _draw_calendar_marks(ax, events)
        _plot_partner_lines(
            ax, indices[indices["country"] == country], INDEX_IMPORT, BILATERAL_PARTNERS
        )
        _annotate_event_names(
            ax, events, skip_regional=False, fontsize=6.5, use_short=False
        )
        ax.set_title(display_country(country))
        _style_share_axis(ax, ylabel="I" if i % 2 == 0 else None)
    for ax in axes.flat[len(countries[:4]) :]:
        ax.set_visible(False)
    for ax in axes[-1, :]:
        if ax.get_visible():
            ax.set_xlabel("Year")
    extra = _overlay_legend_handles()
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles + extra,
        labels + [handle.get_label() for handle in extra],
        loc="upper center",
        ncol=3,
        fontsize=8,
        bbox_to_anchor=(0.5, 1.02),
    )
    fig.suptitle("BACI import index I with event overlay", y=1.06, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, "worked_examples_import_index_events.png")


def generate_overlay_plots(
    indices: pd.DataFrame,
    calendar: pd.DataFrame,
    disasters: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """Write I/E/CWI/CWE country grids plus a four-country worked example."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.png"):
        stale.unlink()
    if indices.empty:
        return []
    paths: list[Path] = []
    for value_col, title, stem in PLOT_SPECS:
        if value_col not in indices.columns:
            continue
        frame = indices[["country", "year", "partner", value_col]].dropna(
            subset=[value_col]
        )
        if frame.empty:
            continue
        paths.append(
            plot_index_with_events(
                frame,
                calendar,
                disasters,
                value_col,
                output_dir,
                title=title,
                filename=f"{stem}.png",
            )
        )
    paths.append(plot_worked_examples(indices, calendar, disasters, output_dir))
    return paths
