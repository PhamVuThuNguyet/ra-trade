import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    FLOW_EXPORT,
    FLOW_IMPORT,
    IMF_PARTNER_COLUMNS,
    PARTNER_US,
    PARTNER_WORLD,
    USD_TO_MILLIONS,
    VALUATION_CIF_FOB_ONLY,
    VALUATION_PRIMARY,
    VALUATION_STANDARD,
    canonical_comtrade_country,
)


def trade_value_usd(row: pd.Series, method: str = VALUATION_STANDARD) -> float:
    """Return harmonized trade value in USD for the chosen valuation rule."""
    if method == VALUATION_PRIMARY:
        value = row["primaryValue__US__"]
        return float(value) if pd.notna(value) else 0.0

    if row["flowCode"] == "M":
        value = row["cifvalue__US__"]
        if method == VALUATION_STANDARD and pd.isna(value):
            value = row["primaryValue__US__"]
    else:
        value = row["fobvalue__US__"]
        if method == VALUATION_STANDARD and pd.isna(value):
            value = row["primaryValue__US__"]

    if method == VALUATION_CIF_FOB_ONLY and pd.isna(value):
        return 0.0
    return float(value) if pd.notna(value) else 0.0


def aggregate_comtrade(
    df: pd.DataFrame,
    value_method: str = VALUATION_STANDARD,
) -> pd.DataFrame:
    """Aggregate Comtrade HS records to country-year-flow-partner totals (millions USD)."""
    working = df.copy()
    working["value_usd"] = working.apply(
        lambda row: trade_value_usd(row, method=value_method),
        axis=1,
    )
    working["country"] = working["reporterDesc"].map(canonical_comtrade_country)

    rows: list[dict] = []
    for partner_key, partner_iso in COMTRADE_PARTNER_ISO.items():
        subset = working[working["partnerISO"] == partner_iso]
        if subset.empty:
            continue

        grouped = subset.groupby(["country", "refYear", "flowCode"], as_index=False)[
            "value_usd"
        ].sum()
        for _, record in grouped.iterrows():
            flow = FLOW_IMPORT if record["flowCode"] == "M" else FLOW_EXPORT
            rows.append(
                {
                    "country": record["country"],
                    "year": int(record["refYear"]),
                    "flow": flow,
                    "partner": partner_key,
                    "comtrade_value_musd": record["value_usd"] / USD_TO_MILLIONS,
                }
            )

    return pd.DataFrame(rows)


def melt_imf(imf_df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide IMF DOTS data to long country-year-flow-partner format."""
    rows: list[dict] = []
    for _, record in imf_df.iterrows():
        country = record["country"]
        year = int(record["time_period"])
        for partner, (export_col, import_col) in IMF_PARTNER_COLUMNS.items():
            export_value = record[export_col]
            if pd.notna(export_value):
                rows.append(
                    {
                        "country": country,
                        "year": year,
                        "flow": FLOW_EXPORT,
                        "partner": partner,
                        "imf_value_musd": float(export_value),
                    }
                )
            import_value = record[import_col]
            if pd.notna(import_value):
                rows.append(
                    {
                        "country": country,
                        "year": year,
                        "flow": FLOW_IMPORT,
                        "partner": partner,
                        "imf_value_musd": float(import_value),
                    }
                )
    return pd.DataFrame(rows)


def merge_sources(
    comtrade_long: pd.DataFrame,
    imf_long: pd.DataFrame,
    country_map: dict[str, str],
) -> pd.DataFrame:
    """Join harmonized Comtrade and IMF observations on shared keys."""
    comtrade = comtrade_long.copy()
    comtrade["imf_country"] = comtrade["country"].map(country_map)
    comtrade = comtrade.dropna(subset=["imf_country"])

    merged = comtrade.merge(
        imf_long,
        left_on=["imf_country", "year", "flow", "partner"],
        right_on=["country", "year", "flow", "partner"],
        how="inner",
        suffixes=("_comtrade", "_imf"),
    )
    merged["country"] = merged["imf_country"]
    merged = merged.drop(columns=["imf_country", "country_imf"], errors="ignore")
    return merged.sort_values(["country", "year", "flow", "partner"]).reset_index(
        drop=True
    )


def flag_comtrade_availability(
    comtrade_long: pd.DataFrame, imf_long: pd.DataFrame
) -> pd.DataFrame:
    """Identify IMF rows with no Comtrade counterpart (e.g. bilateral US in this extract)."""
    comtrade_keys = comtrade_long.assign(imf_country=comtrade_long["country"])[
        ["imf_country", "year", "flow", "partner"]
    ].drop_duplicates()

    imf_keys = imf_long.rename(columns={"country": "imf_country"})
    availability = imf_keys.merge(
        comtrade_keys,
        on=["imf_country", "year", "flow", "partner"],
        how="left",
        indicator=True,
    )
    availability["comtrade_available"] = availability["_merge"] == "both"
    return availability.drop(columns="_merge")
