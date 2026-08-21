"""Metadata discrepancy tables for Comtrade vs IMF."""

from __future__ import annotations

import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    COMTRADE_TO_IMF_COUNTRY,
    COVERAGE_SUMMARY_COLUMNS,
    IMF_PARTNER_COLUMNS,
    PARTNER_US,
    display_comtrade_country,
)
from trade_discrepancy.metadata_tables import (
    build_classification_grain,
    build_reporter_coverage,
    build_schema_comparison,
    build_valuation_completeness,
)


def _unique_sorted_strings(series: pd.Series) -> list[str]:
    return sorted(series.dropna().astype(str).unique().tolist())


def _years(series: pd.Series) -> list[int]:
    return sorted(
        pd.to_numeric(series, errors="coerce").dropna().astype(int).unique().tolist()
    )


def _format_year_span(years: list[int]) -> str:
    if not years:
        return "none"
    return f"{years[0]}-{years[-1]}"


def _missing_years(years: list[int]) -> list[int]:
    if len(years) < 2:
        return []
    return [year for year in range(years[0], years[-1] + 1) if year not in set(years)]


def _comtrade_working(comtrade_raw: pd.DataFrame) -> pd.DataFrame:
    working = comtrade_raw.copy()
    working["country"] = working["reporterDesc"].map(display_comtrade_country)
    working["year"] = pd.to_numeric(working["refYear"], errors="coerce")
    return working


def build_metadata_attribute_comparison(
    comtrade_raw: pd.DataFrame,
    imf_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Side-by-side metadata attributes for the Comtrade extract and IMF DOTS."""
    working = _comtrade_working(comtrade_raw)
    extracts = _unique_sorted_strings(working["comtrade_extract"])
    partners = _unique_sorted_strings(working["partnerISO"])
    classifs = _unique_sorted_strings(working["classificationCode"])
    freqs = _unique_sorted_strings(working["freqCode"])
    years = _years(working["year"])
    reporters = sorted(
        country
        for country in working["country"].dropna().unique()
        if country in COMTRADE_TO_IMF_COUNTRY
    )
    imf_years = _years(imf_raw["time_period"])
    imf_countries = _unique_sorted_strings(imf_raw["country"])
    usa_in_extract = PARTNER_US in COMTRADE_PARTNER_ISO and "USA" in partners

    rows = [
        {
            "attribute": "publisher_concept",
            "comtrade": "UN Comtrade customs/merchandise trade",
            "imf": "IMF Direction of Trade Statistics (DOTS)",
            "discrepancy_flag": "conceptual_source_difference",
            "notes": "Different compilation systems; not identical concepts",
        },
        {
            "attribute": "frequency",
            "comtrade": ",".join(freqs) if freqs else "unknown",
            "imf": "A (annual file)",
            "discrepancy_flag": "none" if freqs == ["A"] else "frequency_mismatch",
            "notes": "Analysis uses annual observations only",
        },
        {
            "attribute": "classification",
            "comtrade": ",".join(classifs) if classifs else "unknown",
            "imf": "partner aggregates (no commodity codes)",
            "discrepancy_flag": "commodity_detail_asymmetry",
            "notes": "Comtrade is commodity-level then aggregated; IMF is pre-aggregated",
        },
        {
            "attribute": "valuation",
            "comtrade": "CIF imports / FOB exports (primaryValue fallback)",
            "imf": "DOTS partner totals (valuation not itemized in extract)",
            "discrepancy_flag": "valuation_documentation_gap",
            "notes": "May contribute to residual world-total gaps",
        },
        {
            "attribute": "units",
            "comtrade": "USD (converted to millions in harmonization)",
            "imf": "millions USD",
            "discrepancy_flag": "none",
            "notes": "Aligned to MUSD before comparison",
        },
        {
            "attribute": "comtrade_extract",
            "comtrade": "; ".join(extracts) if extracts else "none",
            "imf": "n/a",
            "discrepancy_flag": "multi_extract" if len(extracts) > 1 else "none",
            "notes": "Premium API SITC Rev.4 AG3 extract",
        },
        {
            "attribute": "temporal_coverage",
            "comtrade": _format_year_span(years),
            "imf": _format_year_span(imf_years),
            "discrepancy_flag": "temporal_coverage_gap",
            "notes": "IMF starts earlier; Comtrade coverage is still uneven by country",
        },
        {
            "attribute": "reporter_coverage_overlap",
            "comtrade": f"{len(reporters)} mapped PICs with rows",
            "imf": f"{len(imf_countries)} Pacific economies in extract",
            "discrepancy_flag": "reporter_coverage_gap",
            "notes": f"Mapped overlap set size: {len(COMTRADE_TO_IMF_COUNTRY)}",
        },
        {
            "attribute": "partner_codes",
            "comtrade": ",".join(partners),
            "imf": ",".join(sorted(IMF_PARTNER_COLUMNS)),
            "discrepancy_flag": "none" if usa_in_extract else "partner_coverage_asymmetric",
            "notes": "USA bilateral comparable only where Comtrade has USA rows",
        },
        {
            "attribute": "schema_value_fields",
            "comtrade": "cifvalue__US__ / fobvalue__US__ / primaryValue__US__ (normalized)",
            "imf": "exports_* / imports_* wide columns",
            "discrepancy_flag": "schema_difference",
            "notes": "API extract originally used unsuffixed cifvalue/fobvalue/primaryValue",
        },
    ]
    return pd.DataFrame(rows)


def build_metadata_coverage_by_country(
    comtrade_raw: pd.DataFrame,
    imf_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Per-country metadata coverage contrasting Comtrade with IMF."""
    working = _comtrade_working(comtrade_raw)
    imf_years_by_country = {
        country: _years(imf_raw.loc[imf_raw["country"] == country, "time_period"])
        for country in imf_raw["country"].dropna().unique()
    }

    rows: list[dict] = []
    for comtrade_country, imf_country in COMTRADE_TO_IMF_COUNTRY.items():
        subset = working[working["country"] == comtrade_country]
        comtrade_years = _years(subset["year"])
        imf_years = imf_years_by_country.get(imf_country, [])
        overlap = sorted(set(comtrade_years) & set(imf_years))
        missing = _missing_years(comtrade_years)
        partners = _unique_sorted_strings(subset["partnerISO"])
        extracts = _unique_sorted_strings(subset["comtrade_extract"])
        has_usa = "USA" in partners
        rows.append(
            {
                "country": imf_country,
                "comtrade_country": comtrade_country,
                "comtrade_extracts": ", ".join(extracts),
                "comtrade_year_min": min(comtrade_years) if comtrade_years else None,
                "comtrade_year_max": max(comtrade_years) if comtrade_years else None,
                "comtrade_n_years": len(comtrade_years),
                "comtrade_missing_years": ", ".join(str(year) for year in missing),
                "imf_year_min": min(imf_years) if imf_years else None,
                "imf_year_max": max(imf_years) if imf_years else None,
                "imf_n_years": len(imf_years),
                "overlap_years": len(overlap),
                "overlap_year_min": overlap[0] if overlap else None,
                "overlap_year_max": overlap[-1] if overlap else None,
                "comtrade_partners": ",".join(partners),
                "has_comtrade_usa": has_usa,
                "usa_comparable": has_usa,
                "metadata_gap_notes": "; ".join(
                    note
                    for note in [
                        "no_comtrade_rows" if not comtrade_years else "",
                        "short_overlap" if 0 < len(overlap) < 5 else "",
                        "usa_missing_in_comtrade" if not has_usa else "",
                        "multi_extract" if len(extracts) > 1 else "",
                        "gaps_within_span" if missing else "",
                    ]
                    if note
                ),
            }
        )
    return pd.DataFrame(rows)


def coverage_summary_from_metadata(metadata_coverage: pd.DataFrame) -> pd.DataFrame:
    """Overlap-year view used by the coverage layer (subset of metadata coverage)."""
    return metadata_coverage.loc[:, list(COVERAGE_SUMMARY_COLUMNS)].copy()


def build_metadata_discrepancy_flags(
    attribute_comparison: pd.DataFrame,
    coverage_by_country: pd.DataFrame,
) -> pd.DataFrame:
    """Flatten metadata mismatches into an alert-oriented flag table."""
    rows: list[dict] = []
    for record in attribute_comparison.itertuples(index=False):
        if record.discrepancy_flag == "none":
            continue
        rows.append(
            {
                "scope": "source_pair",
                "entity": "Comtrade vs IMF",
                "flag": record.discrepancy_flag,
                "attribute": record.attribute,
                "detail": record.notes,
            }
        )

    for record in coverage_by_country.itertuples(index=False):
        notes = [
            part.strip()
            for part in str(record.metadata_gap_notes).split(";")
            if part.strip()
        ]
        for note in notes:
            rows.append(
                {
                    "scope": "country",
                    "entity": record.comtrade_country,
                    "flag": note,
                    "attribute": "coverage",
                    "detail": (
                        f"overlap_years={record.overlap_years}; "
                        f"partners={record.comtrade_partners}; "
                        f"extracts={record.comtrade_extracts}; "
                        f"missing_years={record.comtrade_missing_years}"
                    ),
                }
            )
    return pd.DataFrame(rows)


def run_metadata_discrepancy_analysis(
    comtrade_raw: pd.DataFrame,
    imf_raw: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Run the metadata discrepancy layer and return output tables."""
    working = _comtrade_working(comtrade_raw)
    mapped = working[working["country"].isin(COMTRADE_TO_IMF_COUNTRY)].copy()
    attributes = build_metadata_attribute_comparison(comtrade_raw, imf_raw)
    coverage = build_metadata_coverage_by_country(comtrade_raw, imf_raw)
    flags = build_metadata_discrepancy_flags(attributes, coverage)
    return {
        "metadata_attributes": attributes,
        "metadata_coverage": coverage,
        "metadata_flags": flags,
        "valuation_completeness": build_valuation_completeness(mapped),
        "schema_comparison": build_schema_comparison(comtrade_raw, imf_raw),
        "classification_grain": build_classification_grain(mapped),
        "reporter_coverage": build_reporter_coverage(working, imf_raw),
    }
