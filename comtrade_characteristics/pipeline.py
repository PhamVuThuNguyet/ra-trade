"""End-to-end characterization of the Comtrade Premium API extract."""

from pathlib import Path

from comtrade_characteristics.constants import (
    EXTRACT_DIR,
    OUTPUT_DIR,
    OUTPUT_FILENAME,
    REQUESTED_YEARS,
)
from comtrade_characteristics.summarize import (
    availability_by_year,
    flow_by_year,
    overview,
    partner_by_year,
    partner_gaps,
    prepare_extract,
    reporter_summary,
    reporter_year_panel,
    value_completeness,
)
from trade_discrepancy.loaders import load_comtrade

CORE_OUTPUT_FILES = (
    "overview.csv",
    "availability_by_year.csv",
    "reporter_summary.csv",
    "reporter_year_panel.csv",
    "flow_by_year.csv",
    "partner_by_year.csv",
    "value_completeness.csv",
    "partner_gaps.csv",
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    root = Path(output_dir)
    csv_dir = root / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir


def run_analysis(
    output_dir: Path = OUTPUT_DIR,
    *,
    extract_dir: Path = EXTRACT_DIR,
    extract_filename: str = OUTPUT_FILENAME,
) -> dict:
    """Describe coverage of the SITC Rev.4 AG3 API extract (not portal CSVs)."""
    output_dir, csv_dir = resolve_output_dirs(output_dir)
    raw = load_comtrade(comtrade_dir=extract_dir, filenames=[extract_filename])
    working = prepare_extract(raw)

    overview_table = overview(working)
    availability = availability_by_year(working, years=REQUESTED_YEARS)
    summary = reporter_summary(working)
    panel = reporter_year_panel(working)
    flows = flow_by_year(working)
    partners = partner_by_year(working)
    completeness = value_completeness(working)
    gaps = partner_gaps(working)

    overview_table.to_csv(csv_dir / "overview.csv", index=False)
    availability.to_csv(csv_dir / "availability_by_year.csv", index=False)
    summary.to_csv(csv_dir / "reporter_summary.csv", index=False)
    panel.to_csv(csv_dir / "reporter_year_panel.csv", index=False)
    flows.to_csv(csv_dir / "flow_by_year.csv", index=False)
    partners.to_csv(csv_dir / "partner_by_year.csv", index=False)
    completeness.to_csv(csv_dir / "value_completeness.csv", index=False)
    gaps.to_csv(csv_dir / "partner_gaps.csv", index=False)

    present_years = (
        availability.loc[availability["n_records"] > 0, "year"].tolist()
        if not availability.empty
        else []
    )
    return {
        "n_records": len(working),
        "n_reporters_observed": int(summary["observed"].sum()),
        "n_reporters_requested": len(summary),
        "year_min": int(min(present_years)) if present_years else None,
        "year_max": int(max(present_years)) if present_years else None,
        "n_years_observed": len(present_years),
        "n_partner_gaps": len(gaps),
        "overview": overview_table,
        "availability": availability,
        "reporter_summary": summary,
        "reporter_year_panel": panel,
        "flow_by_year": flows,
        "partner_by_year": partners,
        "value_completeness": completeness,
        "partner_gaps": gaps,
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
    }
