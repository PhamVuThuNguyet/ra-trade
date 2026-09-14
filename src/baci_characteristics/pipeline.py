"""End-to-end characterization of CEPII BACI HS02 (Pacific Island slice)."""

from pathlib import Path

from baci.constants import BACI_DIR, CACHE_DIR
from baci.loaders import load_country_codes, load_pic_flows, load_product_codes
from baci_characteristics.constants import OUTPUT_DIR, REQUESTED_YEARS
from baci_characteristics.summarize import (
    availability_by_year,
    flow_by_year,
    overview,
    partner_by_year,
    partner_gaps,
    prepare_pic_view,
    product_coverage,
    reporter_summary,
    reporter_year_panel,
    value_quantity_completeness,
)

CORE_OUTPUT_FILES = (
    "overview.csv",
    "year_stats.csv",
    "availability_by_year.csv",
    "reporter_summary.csv",
    "reporter_year_panel.csv",
    "flow_by_year.csv",
    "partner_by_year.csv",
    "value_quantity_completeness.csv",
    "partner_gaps.csv",
    "product_coverage.csv",
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    root = Path(output_dir)
    csv_dir = root / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir


def run_analysis(
    output_dir: Path = OUTPUT_DIR,
    *,
    baci_dir: Path = BACI_DIR,
    use_cache: bool = True,
    cache_dir: Path = CACHE_DIR,
) -> dict:
    """Describe full BACI year-file coverage and the PIC reporter view."""
    output_dir, csv_dir = resolve_output_dirs(output_dir)
    country_codes = load_country_codes(baci_dir)
    product_codes = load_product_codes(baci_dir)
    pic_flows, year_stats = load_pic_flows(
        baci_dir, use_cache=use_cache, cache_dir=cache_dir
    )
    working = prepare_pic_view(pic_flows, country_codes)

    overview_table = overview(
        working,
        year_stats,
        n_countries_meta=len(country_codes),
        n_products_meta=len(product_codes),
    )
    availability = availability_by_year(working, years=REQUESTED_YEARS)
    summary = reporter_summary(working)
    panel = reporter_year_panel(working)
    flows = flow_by_year(working)
    partners = partner_by_year(working)
    completeness = value_quantity_completeness(working)
    gaps = partner_gaps(working)
    products = product_coverage(working)

    overview_table.to_csv(csv_dir / "overview.csv", index=False)
    year_stats.to_csv(csv_dir / "year_stats.csv", index=False)
    availability.to_csv(csv_dir / "availability_by_year.csv", index=False)
    summary.to_csv(csv_dir / "reporter_summary.csv", index=False)
    panel.to_csv(csv_dir / "reporter_year_panel.csv", index=False)
    flows.to_csv(csv_dir / "flow_by_year.csv", index=False)
    partners.to_csv(csv_dir / "partner_by_year.csv", index=False)
    completeness.to_csv(csv_dir / "value_quantity_completeness.csv", index=False)
    gaps.to_csv(csv_dir / "partner_gaps.csv", index=False)
    products.to_csv(csv_dir / "product_coverage.csv", index=False)

    present_years = (
        availability.loc[availability["n_records"] > 0, "year"].tolist()
        if not availability.empty
        else []
    )
    return {
        "n_records_full": int(year_stats["n_records"].sum()) if not year_stats.empty else 0,
        "n_records_pic_view": len(working),
        "n_reporters_observed": int(summary["observed"].sum()),
        "n_reporters_requested": len(summary),
        "year_min": int(min(present_years)) if present_years else None,
        "year_max": int(max(present_years)) if present_years else None,
        "n_years_observed": len(present_years),
        "n_partner_gaps": len(gaps),
        "overview": overview_table,
        "year_stats": year_stats,
        "availability": availability,
        "reporter_summary": summary,
        "reporter_year_panel": panel,
        "flow_by_year": flows,
        "partner_by_year": partners,
        "value_quantity_completeness": completeness,
        "partner_gaps": gaps,
        "product_coverage": products,
        "pic_flows": pic_flows,
        "working": working,
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
    }
