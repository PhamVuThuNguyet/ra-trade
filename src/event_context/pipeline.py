"""Merge the PIC event calendar, Lowy aid, and EM-DAT onto BACI indices."""

from pathlib import Path

import pandas as pd
import requests

from event_context.calendar import load_calendar
from event_context.constants import (
    CORE_OUTPUT_FILES,
    INDICES_BACI_PATH,
    INDICES_EVENTS_SIDECAR,
    OUTPUT_DIR,
)
from event_context.emdat import load_emdat
from event_context.lowy import load_lowy_aid
from event_context.merge import coverage_summary, merge_all
from event_context.visualize import generate_overlay_plots
from trade_influence.pipeline import resolve_output_dirs


def run_overlay(
    output_dir: Path = OUTPUT_DIR,
    *,
    indices_path: Path = INDICES_BACI_PATH,
    indices: pd.DataFrame | None = None,
    fetch_remote: bool = True,
    aid: pd.DataFrame | None = None,
    disasters: pd.DataFrame | None = None,
    write_sidecar: bool = True,
) -> dict:
    """
    Left-join calendar flags, Lowy partner aid, and EM-DAT onto indices_baci.

    The original ``outputs/baci_influence/csv/indices_baci.csv`` is not
    overwritten. The merged panel is written to ``outputs/baci_events/csv/``
    and copied beside the influence file as ``indices_baci_events.csv``.
    """
    root, csv_dir, plots_dir = resolve_output_dirs(output_dir)
    if indices is None:
        indices = pd.read_csv(indices_path)
    calendar = load_calendar()
    lowy_source = "supplied"
    emdat_source = "supplied"
    if aid is None:
        aid, lowy_source = load_lowy_aid(fetch_remote=fetch_remote)
    if disasters is None:
        try:
            disasters, emdat_source = load_emdat(fetch_remote=fetch_remote)
        except (OSError, ValueError, KeyError, requests.RequestException):
            disasters = pd.DataFrame()
            emdat_source = "emdat_missing"

    merged = merge_all(indices, calendar, aid, disasters)
    if len(merged) != len(indices):
        raise ValueError(
            f"Overlay changed row count: {len(indices)} -> {len(merged)}"
        )
    summary = coverage_summary(
        merged,
        lowy_source=lowy_source,
        emdat_source=emdat_source,
        n_calendar_events=len(calendar),
    )

    calendar.to_csv(csv_dir / "event_calendar.csv", index=False)
    aid.to_csv(csv_dir / "lowy_aid_by_partner.csv", index=False)
    disasters.to_csv(csv_dir / "emdat_by_country_year.csv", index=False)
    merged.to_csv(csv_dir / "indices_baci.csv", index=False)
    summary.to_csv(csv_dir / "coverage_summary.csv", index=False)
    if write_sidecar:
        INDICES_EVENTS_SIDECAR.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(INDICES_EVENTS_SIDECAR, index=False)

    plot_paths = generate_overlay_plots(merged, calendar, disasters, plots_dir)

    return {
        "n_index_rows": len(merged),
        "n_calendar_events": len(calendar),
        "lowy_source": lowy_source,
        "emdat_source": emdat_source,
        "output_dir": str(root),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "sidecar": str(INDICES_EVENTS_SIDECAR) if write_sidecar else None,
        "indices": merged,
        "calendar": calendar,
        "aid": aid,
        "disasters": disasters,
        "summary": summary,
        "plots": [str(path) for path in plot_paths],
        "files": CORE_OUTPUT_FILES,
    }
