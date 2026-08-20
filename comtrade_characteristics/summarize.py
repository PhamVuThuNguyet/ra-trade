"""Tables describing coverage and completeness of the Comtrade API extract."""

from collections.abc import Sequence

import pandas as pd

from comtrade_characteristics.constants import (
    EXPECTED_PARTNERS,
    FLOW_LABELS,
    REPORTER_ISO_BY_DISPLAY,
    REQUESTED_REPORTERS,
    REQUESTED_YEARS,
)
from trade_discrepancy.constants import display_comtrade_country


def prepare_extract(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach display country names and integer years."""
    working = frame.copy()
    working["year"] = pd.to_numeric(working["refYear"], errors="coerce")
    working["country"] = working["reporterDesc"].map(display_comtrade_country)
    working = working.dropna(subset=["year", "country"])
    working["year"] = working["year"].astype(int)
    return working


def availability_by_year(
    working: pd.DataFrame,
    years: Sequence[int] | None = None,
) -> pd.DataFrame:
    """Year-by-year record counts and reporters present in the extract."""
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
    reporters: Sequence[str] = REQUESTED_REPORTERS,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    """Full requested reporter × year grid with presence and record counts."""
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
    merged["iso3"] = merged["country"].map(REPORTER_ISO_BY_DISPLAY)
    return merged


def reporter_summary(
    working: pd.DataFrame,
    reporters: Sequence[str] = REQUESTED_REPORTERS,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    """One row per requested reporter, including economies with no published rows."""
    rows: list[dict] = []
    n_requested_years = len(years)
    for country in reporters:
        group = working[working["country"] == country]
        observed_years = sorted(group["year"].unique().tolist()) if not group.empty else []
        partners = (
            ",".join(sorted(group["partnerISO"].dropna().astype(str).unique()))
            if not group.empty
            else ""
        )
        flows = (
            ",".join(sorted(group["flowCode"].dropna().astype(str).unique()))
            if not group.empty
            else ""
        )
        n_cmd = int(group["cmdCode"].nunique()) if "cmdCode" in group.columns else 0
        rows.append(
            {
                "country": country,
                "iso3": REPORTER_ISO_BY_DISPLAY.get(country, ""),
                "observed": not group.empty,
                "n_records": int(len(group)),
                "n_years": len(observed_years),
                "n_requested_years": n_requested_years,
                "year_share": len(observed_years) / n_requested_years if n_requested_years else 0.0,
                "year_min": observed_years[0] if observed_years else pd.NA,
                "year_max": observed_years[-1] if observed_years else pd.NA,
                "years": ",".join(str(year) for year in observed_years),
                "n_cmd": n_cmd,
                "partners": partners,
                "flows": flows,
            }
        )
    return pd.DataFrame(rows)


def flow_by_year(working: pd.DataFrame) -> pd.DataFrame:
    counts = (
        working.groupby(["year", "flowCode"], as_index=False)
        .size()
        .rename(columns={"size": "n_records"})
    )
    counts["flow"] = counts["flowCode"].map(FLOW_LABELS).fillna(counts["flowCode"])
    return counts.sort_values(["year", "flowCode"]).reset_index(drop=True)


def partner_by_year(working: pd.DataFrame) -> pd.DataFrame:
    return (
        working.groupby(["year", "partnerISO"], as_index=False)
        .size()
        .rename(columns={"size": "n_records"})
        .sort_values(["year", "partnerISO"])
        .reset_index(drop=True)
    )


def value_completeness(working: pd.DataFrame) -> pd.DataFrame:
    """CIF / FOB / primary value non-null shares by flow."""
    value_cols = [
        col
        for col in ("cifvalue__US__", "fobvalue__US__", "primaryValue__US__")
        if col in working.columns
    ]
    rows: list[dict] = []
    for flow_code, group in working.groupby("flowCode", sort=True):
        row = {
            "flowCode": flow_code,
            "flow": FLOW_LABELS.get(str(flow_code), str(flow_code)),
            "n_records": int(len(group)),
        }
        for col in value_cols:
            present = pd.to_numeric(group[col], errors="coerce").notna()
            row[f"{col}_n"] = int(present.sum())
            row[f"{col}_share"] = float(present.mean()) if len(group) else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def partner_gaps(
    working: pd.DataFrame,
    expected_partners: Sequence[str] = EXPECTED_PARTNERS,
) -> pd.DataFrame:
    """Country–year–flow cells that do not contain every requested partner."""
    expected = tuple(sorted(expected_partners))
    grouped = (
        working.groupby(["country", "year", "flowCode"], as_index=False)["partnerISO"]
        .agg(lambda series: tuple(sorted(series.dropna().astype(str).unique())))
        .rename(columns={"partnerISO": "partners"})
    )
    grouped["n_partners"] = grouped["partners"].map(len)
    grouped["missing_partners"] = grouped["partners"].map(
        lambda present: ",".join(code for code in expected if code not in present)
    )
    grouped["partners"] = grouped["partners"].map(lambda present: ",".join(present))
    grouped["flow"] = grouped["flowCode"].map(FLOW_LABELS).fillna(grouped["flowCode"])
    return grouped[grouped["missing_partners"] != ""].reset_index(drop=True)


def overview(
    working: pd.DataFrame,
    reporters: Sequence[str] = REQUESTED_REPORTERS,
    years: Sequence[int] = REQUESTED_YEARS,
) -> pd.DataFrame:
    """Key-value snapshot of extract dimensions versus the API request."""
    observed_year_set = set(working["year"].unique()) if not working.empty else set()
    observed_country_set = set(working["country"].unique()) if not working.empty else set()
    observed_years = [year for year in years if year in observed_year_set]
    observed_reporters = [name for name in reporters if name in observed_country_set]
    absent_reporters = [name for name in reporters if name not in observed_country_set]
    panel = reporter_year_panel(working, reporters, years)
    n_present = int(panel["present"].sum())
    n_requested_cells = len(reporters) * len(years)
    cmd_n = int(working["cmdCode"].nunique()) if "cmdCode" in working.columns else 0
    rows = [
        ("n_records", len(working), "Commodity-level rows in the extract"),
        ("n_years_requested", len(years), f"{years[0]}–{years[-1]}" if years else ""),
        (
            "n_years_observed",
            len(observed_years),
            f"{observed_years[0]}–{observed_years[-1]}" if observed_years else "none",
        ),
        (
            "n_years_empty",
            len([year for year in years if year not in observed_years]),
            "Requested years with zero rows",
        ),
        ("n_reporters_requested", len(reporters), ""),
        ("n_reporters_observed", len(observed_reporters), ", ".join(observed_reporters)),
        (
            "n_reporters_absent",
            len(absent_reporters),
            ", ".join(absent_reporters),
        ),
        ("n_reporter_years_requested", n_requested_cells, "Reporters × requested years"),
        ("n_reporter_years_observed", n_present, "Cells with at least one row"),
        (
            "reporter_year_coverage",
            round(n_present / n_requested_cells, 4) if n_requested_cells else 0.0,
            "Observed reporter–years / requested",
        ),
        ("n_partners", working["partnerISO"].nunique() if not working.empty else 0, ""),
        ("n_flows", working["flowCode"].nunique() if not working.empty else 0, ""),
        ("n_cmd", cmd_n, "Distinct SITC AG3 codes"),
    ]
    metrics = [row[0] for row in rows]
    values = [row[1] for row in rows]
    notes = [row[2] for row in rows]
    return pd.DataFrame(
        {"metric": metrics, "value": pd.Series(values, dtype="object"), "notes": notes}
    )
