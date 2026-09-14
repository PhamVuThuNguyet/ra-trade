"""Supplementary metadata tables that replace simple diagnostic plots."""

from __future__ import annotations

import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_SCHEMA_KEYS,
    COMTRADE_TO_IMF_COUNTRY,
    FLOW_CODE_EXPORT,
    FLOW_CODE_IMPORT,
    FLOW_EXPORT,
    FLOW_IMPORT,
    IMF_SCHEMA_KEYS,
)

VALUATION_FIELD_LABELS = {
    "cifvalue__US__": "CIF",
    "fobvalue__US__": "FOB",
    "primaryValue__US__": "primary",
}


def build_valuation_completeness(mapped: pd.DataFrame) -> pd.DataFrame:
    """Share of mapped Comtrade rows with CIF / FOB / primary values, by flow."""
    flow_labels = {FLOW_CODE_IMPORT: FLOW_IMPORT, FLOW_CODE_EXPORT: FLOW_EXPORT}
    rows: list[dict] = []
    for flow_code, flow_label in flow_labels.items():
        subset = mapped[mapped["flowCode"] == flow_code]
        if subset.empty:
            continue
        n_records = len(subset)
        for column, field in VALUATION_FIELD_LABELS.items():
            if column not in subset.columns:
                continue
            n_present = int(subset[column].notna().sum())
            rows.append(
                {
                    "flow": flow_label,
                    "field": field,
                    "n_records": n_records,
                    "n_present": n_present,
                    "missing_share": 1.0 - (n_present / n_records),
                }
            )
    return pd.DataFrame(rows)


def build_schema_comparison(
    comtrade_raw: pd.DataFrame,
    imf_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Which comparison keys are present in each source extract."""
    rows = [
        {
            "source": "comtrade",
            "field": field,
            "present": field in comtrade_raw.columns,
        }
        for field in COMTRADE_SCHEMA_KEYS
    ]
    rows.extend(
        {
            "source": "imf",
            "field": field,
            "present": field in imf_raw.columns,
        }
        for field in IMF_SCHEMA_KEYS
    )
    return pd.DataFrame(rows)


def build_classification_grain(mapped: pd.DataFrame) -> pd.DataFrame:
    """Commodity-level density by mapped reporter (vs IMF partner aggregates)."""
    if mapped.empty:
        return pd.DataFrame(
            columns=["country", "n_records", "n_commodity_codes", "n_years", "n_partners"]
        )
    return (
        mapped.groupby("country", as_index=False)
        .agg(
            n_records=("cmdCode", "size"),
            n_commodity_codes=("cmdCode", "nunique"),
            n_years=("year", "nunique"),
            n_partners=("partnerISO", "nunique"),
        )
        .sort_values("country")
        .reset_index(drop=True)
    )


def build_reporter_coverage(
    working: pd.DataFrame,
    imf_raw: pd.DataFrame,
) -> pd.DataFrame:
    """IMF Pacific economies vs mapped Comtrade reporters, including unmatched sets."""
    comtrade_countries = set(working["country"].dropna())
    imf_countries = set(imf_raw["country"].dropna())
    mapped_imf = set(COMTRADE_TO_IMF_COUNTRY.values())
    mapped_comtrade = set(COMTRADE_TO_IMF_COUNTRY)

    rows: list[dict] = []
    for comtrade_country, imf_country in COMTRADE_TO_IMF_COUNTRY.items():
        rows.append(
            {
                "economy": comtrade_country,
                "imf_name": imf_country,
                "in_imf": imf_country in imf_countries,
                "in_comtrade": comtrade_country in comtrade_countries,
                "status": "comparable",
            }
        )
    for imf_country in sorted(imf_countries - mapped_imf):
        rows.append(
            {
                "economy": imf_country,
                "imf_name": imf_country,
                "in_imf": True,
                "in_comtrade": False,
                "status": "imf_only",
            }
        )
    for comtrade_country in sorted(comtrade_countries - mapped_comtrade):
        rows.append(
            {
                "economy": comtrade_country,
                "imf_name": "",
                "in_imf": False,
                "in_comtrade": True,
                "status": "comtrade_unmapped",
            }
        )
    return pd.DataFrame(rows)
