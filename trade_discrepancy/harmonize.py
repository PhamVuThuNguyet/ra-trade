import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    FLOW_CODE_IMPORT,
    FLOW_EXPORT,
    FLOW_IMPORT,
    IMF_PARTNER_COLUMNS,
    USD_TO_MILLIONS,
    VALUATION_CIF_FOB_ONLY,
    VALUATION_PRIMARY,
    VALUATION_STANDARD,
    canonical_comtrade_country,
)


def trade_value_series(
    frame: pd.DataFrame,
    method: str = VALUATION_STANDARD,
) -> pd.Series:
    """Vectorized CIF/FOB valuation with optional primaryValue fallback."""
    if method == VALUATION_PRIMARY:
        return pd.to_numeric(frame["primaryValue__US__"], errors="coerce").fillna(0.0)

    is_import = frame["flowCode"].eq(FLOW_CODE_IMPORT)
    cif = pd.to_numeric(frame["cifvalue__US__"], errors="coerce")
    fob = pd.to_numeric(frame["fobvalue__US__"], errors="coerce")
    primary = pd.to_numeric(frame["primaryValue__US__"], errors="coerce")
    value = cif.where(is_import, fob)

    if method == VALUATION_STANDARD:
        value = value.fillna(primary)
    elif method != VALUATION_CIF_FOB_ONLY:
        raise ValueError(f"Unknown valuation method: {method}")

    return value.fillna(0.0)


def trade_value_usd(row: pd.Series, method: str = VALUATION_STANDARD) -> float:
    """Return harmonized trade value in USD for a single Comtrade record."""
    return float(trade_value_series(pd.DataFrame([row]), method=method).iloc[0])


def aggregate_comtrade(
    df: pd.DataFrame,
    value_method: str = VALUATION_STANDARD,
) -> pd.DataFrame:
    """Aggregate commodity records to country-year-flow-partner totals (millions USD)."""
    iso_to_partner = {iso: partner for partner, iso in COMTRADE_PARTNER_ISO.items()}
    working = df.loc[df["partnerISO"].isin(iso_to_partner)].copy()
    if working.empty:
        return pd.DataFrame(
            columns=["country", "year", "flow", "partner", "comtrade_value_musd"]
        )

    working["value_usd"] = trade_value_series(working, method=value_method)
    working["country"] = working["reporterDesc"].map(canonical_comtrade_country)
    working["year"] = pd.to_numeric(working["refYear"], errors="coerce")
    working["flow"] = working["flowCode"].map(
        {FLOW_CODE_IMPORT: FLOW_IMPORT}
    ).fillna(FLOW_EXPORT)
    working["partner"] = working["partnerISO"].map(iso_to_partner)
    working = working.dropna(subset=["country", "year", "flow", "partner"])
    working["year"] = working["year"].astype(int)

    grouped = working.groupby(
        ["country", "year", "flow", "partner"], as_index=False
    )["value_usd"].sum()
    grouped["comtrade_value_musd"] = grouped["value_usd"] / USD_TO_MILLIONS
    return grouped.drop(columns="value_usd")


def melt_imf(imf_df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide IMF DOTS data to long country-year-flow-partner format."""
    frames: list[pd.DataFrame] = []
    years = pd.to_numeric(imf_df["time_period"], errors="coerce")
    for partner, (export_col, import_col) in IMF_PARTNER_COLUMNS.items():
        for flow, column in ((FLOW_EXPORT, export_col), (FLOW_IMPORT, import_col)):
            frame = pd.DataFrame(
                {
                    "country": imf_df["country"],
                    "year": years,
                    "flow": flow,
                    "partner": partner,
                    "imf_value_musd": pd.to_numeric(imf_df[column], errors="coerce"),
                }
            )
            frames.append(frame.dropna(subset=["year", "imf_value_musd"]))

    melted = pd.concat(frames, ignore_index=True)
    melted["year"] = melted["year"].astype(int)
    return melted


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
