"""Tables describing coverage and completeness of CEPII BACI HS02."""

from collections.abc import Sequence

import pandas as pd

from baci.constants import (
    EXPECTED_PARTNER_ISO3,
    HS2_COL,
    PARTNER_BACI_CODES,
    PARTNER_CODE_TO_KEY,
    PIC_DISPLAY_NAMES,
    PIC_ISO3_BY_DISPLAY,
)
from baci.prepare import pic_reporter_view
from baci_characteristics.constants import REQUESTED_YEARS
from trade_discrepancy.constants import PARTNER_AUS, PARTNER_CHN, PARTNER_US

BILATERAL_CODE_TO_ISO3 = {
    PARTNER_BACI_CODES[PARTNER_AUS]: "AUS",
    PARTNER_BACI_CODES[PARTNER_CHN]: "CHN",
    PARTNER_BACI_CODES[PARTNER_US]: "USA",
}


def attach_partner_iso(working: pd.DataFrame, country_codes: pd.DataFrame) -> pd.DataFrame:
    """Add partner ISO3 (and key for AUS/CHN/US) from BACI country metadata."""
    lookup = country_codes.drop_duplicates("country_code").set_index("country_code")
    iso_map = lookup["country_iso3"].to_dict() if "country_iso3" in lookup.columns else {}
    frame = working.copy()
    frame["partner_iso3"] = frame["partner_code"].map(iso_map)
    bilateral_iso = frame["partner_code"].map(BILATERAL_CODE_TO_ISO3)
    frame["partner_iso3"] = bilateral_iso.fillna(frame["partner_iso3"])
    frame["partner_key"] = frame["partner_code"].map(PARTNER_CODE_TO_KEY)
    return frame


def prepare_pic_view(
    flows: pd.DataFrame,
    country_codes: pd.DataFrame,
) -> pd.DataFrame:
    """PIC-as-reporter view with partner ISO codes attached."""
    working = pic_reporter_view(flows)
    if working.empty:
        working["partner_iso3"] = pd.Series(dtype="object")
        working["partner_key"] = pd.Series(dtype="object")
        return working
    return attach_partner_iso(working, country_codes)


def availability_by_year(
    working: pd.DataFrame,
    years: Sequence[int] | None = None,
) -> pd.DataFrame:
    rows: list[dict] = []
    for year, group in working.groupby("year", sort=True):
        countries = sorted(group["country"].unique().tolist())
        rows.append(
            {
                "year": int(year),
                "n_records": int(len(group)),
                "n_reporters": len(countries),
                "reporters": ", ".join(countries),
            }
        )
    observed = pd.DataFrame(rows)
    if years is None:
        return observed
    filled = pd.DataFrame({"year": list(years)})
    merged = filled.merge(observed, on="year", how="left")
    merged["n_records"] = merged["n_records"].fillna(0).astype(int)
    merged["n_reporters"] = merged["n_reporters"].fillna(0).astype(int)
    merged["reporters"] = merged["reporters"].fillna("")
    return merged


def reporter_year_panel(
    working: pd.DataFrame,
    reporters: Sequence[str] = PIC_DISPLAY_NAMES,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    counts = (
        working.groupby(["country", "year"], as_index=False)
        .size()
        .rename(columns={"size": "n_records"})
    )
    grid = pd.MultiIndex.from_product(
        [list(reporters), list(years)], names=["country", "year"]
    ).to_frame(index=False)
    merged = grid.merge(counts, on=["country", "year"], how="left")
    merged["n_records"] = merged["n_records"].fillna(0).astype(int)
    merged["present"] = (merged["n_records"] > 0).astype(int)
    merged["iso3"] = merged["country"].map(PIC_ISO3_BY_DISPLAY)
    return merged


def reporter_summary(
    working: pd.DataFrame,
    reporters: Sequence[str] = PIC_DISPLAY_NAMES,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    rows: list[dict] = []
    n_requested_years = len(years)
    for country in reporters:
        group = working[working["country"] == country]
        observed_years = sorted(group["year"].unique().tolist()) if not group.empty else []
        present_iso = (
            set(group["partner_iso3"].dropna().astype(str)) if not group.empty else set()
        )
        partners = ",".join(
            code for code in EXPECTED_PARTNER_ISO3 if code in present_iso
        )
        flows = (
            ",".join(sorted(group["flow"].dropna().astype(str).unique()))
            if not group.empty
            else ""
        )
        n_hs6 = int(group["hs6"].nunique()) if not group.empty else 0
        n_hs2 = int(group[HS2_COL].nunique()) if not group.empty else 0
        rows.append(
            {
                "country": country,
                "iso3": PIC_ISO3_BY_DISPLAY.get(country, ""),
                "observed": not group.empty,
                "n_records": int(len(group)),
                "n_years": len(observed_years),
                "n_requested_years": n_requested_years,
                "year_share": len(observed_years) / n_requested_years if n_requested_years else 0.0,
                "year_min": observed_years[0] if observed_years else pd.NA,
                "year_max": observed_years[-1] if observed_years else pd.NA,
                "years": ",".join(str(year) for year in observed_years),
                "n_hs6": n_hs6,
                "n_hs2": n_hs2,
                "n_partners": group["partner_code"].nunique() if not group.empty else 0,
                "partners_focus": partners,
                "flows": flows,
            }
        )
    return pd.DataFrame(rows)


def flow_by_year(working: pd.DataFrame) -> pd.DataFrame:
    return (
        working.groupby(["year", "flow"], as_index=False)
        .size()
        .rename(columns={"size": "n_records"})
        .sort_values(["year", "flow"])
        .reset_index(drop=True)
    )


def partner_by_year(working: pd.DataFrame) -> pd.DataFrame:
    focus = working[working["partner_iso3"].isin(EXPECTED_PARTNER_ISO3)]
    if focus.empty:
        return pd.DataFrame(columns=["year", "partner_iso3", "n_records"])
    return (
        focus.groupby(["year", "partner_iso3"], as_index=False)
        .size()
        .rename(columns={"size": "n_records"})
        .sort_values(["year", "partner_iso3"])
        .reset_index(drop=True)
    )


def value_quantity_completeness(working: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    grouped = working.groupby("flow", sort=True) if not working.empty else []
    for flow, group in grouped:
        value = pd.to_numeric(group["value_thousands_usd"], errors="coerce")
        qty = pd.to_numeric(group["quantity_tons"], errors="coerce")
        rows.append(
            {
                "flow": flow,
                "n_records": int(len(group)),
                "value_n": int(value.notna().sum()),
                "value_share": float(value.notna().mean()) if len(group) else 0.0,
                "value_positive_share": float((value > 0).mean()) if len(group) else 0.0,
                "qty_n": int(qty.notna().sum()),
                "qty_share": float(qty.notna().mean()) if len(group) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def partner_gaps(
    working: pd.DataFrame,
    expected_partners: Sequence[str] = EXPECTED_PARTNER_ISO3,
) -> pd.DataFrame:
    expected = tuple(sorted(expected_partners))
    expected_set = set(expected)
    grouped = (
        working.groupby(["country", "year", "flow"], as_index=False)["partner_iso3"]
        .agg(
            lambda series: tuple(
                sorted(
                    code
                    for code in series.dropna().astype(str).unique()
                    if code in expected_set
                )
            )
        )
        .rename(columns={"partner_iso3": "partners"})
    )
    grouped["n_partners"] = grouped["partners"].map(len)
    grouped["missing_partners"] = grouped["partners"].map(
        lambda present: ",".join(code for code in expected if code not in present)
    )
    grouped["partners"] = grouped["partners"].map(lambda present: ",".join(present))
    return grouped[grouped["missing_partners"] != ""].reset_index(drop=True)


def product_coverage(working: pd.DataFrame) -> pd.DataFrame:
    if working.empty:
        return pd.DataFrame(
            columns=["country", "flow", "n_hs6", "n_hs2", "n_records"]
        )
    return (
        working.groupby(["country", "flow"], as_index=False)
        .agg(
            n_hs6=("hs6", "nunique"),
            n_hs2=(HS2_COL, "nunique"),
            n_records=("hs6", "size"),
        )
        .sort_values(["country", "flow"])
        .reset_index(drop=True)
    )


def overview(
    working: pd.DataFrame,
    year_stats: pd.DataFrame,
    *,
    n_countries_meta: int,
    n_products_meta: int,
    reporters: Sequence[str] = PIC_DISPLAY_NAMES,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    observed_year_set = set(working["year"].unique()) if not working.empty else set()
    observed_country_set = set(working["country"].unique()) if not working.empty else set()
    observed_years = [year for year in years if year in observed_year_set]
    observed_reporters = [name for name in reporters if name in observed_country_set]
    absent_reporters = [name for name in reporters if name not in observed_country_set]
    panel = reporter_year_panel(working, reporters, years)
    n_present = int(panel["present"].sum())
    n_requested_cells = len(reporters) * len(years)
    n_hs6 = int(working["hs6"].nunique()) if not working.empty else 0
    n_hs2 = int(working[HS2_COL].nunique()) if not working.empty else 0
    n_full_records = int(year_stats["n_records"].sum()) if not year_stats.empty else 0
    n_pic_raw = int(year_stats["n_pic_records"].sum()) if not year_stats.empty else 0
    full_years = (
        sorted(year_stats["year"].dropna().astype(int).tolist())
        if not year_stats.empty
        else []
    )
    rows = [
        ("n_records_full", n_full_records, "All BACI year-file rows scanned"),
        ("n_records_pic_raw", n_pic_raw, "Rows where exporter or importer is a PIC"),
        ("n_records_pic_view", len(working), "PIC-as-reporter rows (import+export)"),
        ("n_years_files", len(full_years), f"{full_years[0]}–{full_years[-1]}" if full_years else ""),
        ("n_years_requested", len(years), f"{years[0]}–{years[-1]}" if years else ""),
        (
            "n_years_observed",
            len(observed_years),
            f"{observed_years[0]}–{observed_years[-1]}" if observed_years else "none",
        ),
        ("n_countries_meta", n_countries_meta, "Rows in country_codes metadata"),
        ("n_products_meta", n_products_meta, "Rows in product_codes metadata"),
        ("n_reporters_requested", len(reporters), ""),
        ("n_reporters_observed", len(observed_reporters), ", ".join(observed_reporters)),
        ("n_reporters_absent", len(absent_reporters), ", ".join(absent_reporters)),
        ("n_reporter_years_requested", n_requested_cells, "PICs × requested years"),
        ("n_reporter_years_observed", n_present, "Cells with at least one PIC flow"),
        (
            "reporter_year_coverage",
            round(n_present / n_requested_cells, 4) if n_requested_cells else 0.0,
            "Observed PIC–years / requested",
        ),
        ("n_hs6", n_hs6, "Distinct HS-6 codes in the PIC view"),
        ("n_hs2", n_hs2, "Distinct HS-2 chapters in the PIC view"),
        (
            "n_focus_partners",
            working["partner_iso3"].isin(EXPECTED_PARTNER_ISO3).sum() if not working.empty else 0,
            "PIC-view rows with AUS, CHN, or USA",
        ),
    ]
    return pd.DataFrame(
        {
            "metric": [row[0] for row in rows],
            "value": pd.Series([row[1] for row in rows], dtype="object"),
            "notes": [row[2] for row in rows],
        }
    )
