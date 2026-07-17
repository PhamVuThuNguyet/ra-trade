import numpy as np
import pandas as pd

from trade_discrepancy.constants import DISCREPANCY_TOLERANCE_PCT


def add_discrepancy_metrics(comparison: pd.DataFrame) -> pd.DataFrame:
    """Compute absolute, relative, and log-ratio discrepancies."""
    result = comparison.copy()
    result["abs_diff_musd"] = result["imf_value_musd"] - result["comtrade_value_musd"]
    result["symmetric_pct_diff"] = np.where(
        (result["imf_value_musd"].abs() + result["comtrade_value_musd"].abs()) > 0,
        200
        * result["abs_diff_musd"]
        / (result["imf_value_musd"].abs() + result["comtrade_value_musd"].abs()),
        np.nan,
    )
    result["log_ratio"] = np.where(
        (result["imf_value_musd"] > 0) & (result["comtrade_value_musd"] > 0),
        np.log(result["imf_value_musd"] / result["comtrade_value_musd"]),
        np.nan,
    )
    result["within_tolerance"] = result["symmetric_pct_diff"].abs() <= DISCREPANCY_TOLERANCE_PCT
    return result


def summarize_discrepancies(metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate discrepancy statistics by country, flow, and partner."""
    group_cols = ["country", "flow", "partner"]
    return (
        metrics.groupby(group_cols, as_index=False)
        .agg(
            n_observations=("year", "count"),
            mean_abs_diff_musd=("abs_diff_musd", lambda s: s.abs().mean()),
            median_symmetric_pct_diff=("symmetric_pct_diff", "median"),
            mean_symmetric_pct_diff=("symmetric_pct_diff", "mean"),
            max_abs_symmetric_pct_diff=("symmetric_pct_diff", lambda s: s.abs().max()),
            share_within_tolerance=("within_tolerance", "mean"),
        )
        .sort_values(group_cols)
    )


def summarize_by_year(metrics: pd.DataFrame) -> pd.DataFrame:
    """Track temporal evolution of discrepancies."""
    return (
        metrics.groupby(["year", "flow", "partner"], as_index=False)
        .agg(
            n_observations=("country", "count"),
            median_symmetric_pct_diff=("symmetric_pct_diff", "median"),
            mean_abs_diff_musd=("abs_diff_musd", lambda s: s.abs().mean()),
            share_within_tolerance=("within_tolerance", "mean"),
        )
        .sort_values(["year", "flow", "partner"])
    )


def coverage_summary(comtrade_long: pd.DataFrame, imf_long: pd.DataFrame) -> pd.DataFrame:
    """Summarize temporal and partner coverage overlap between sources."""
    from trade_discrepancy.constants import COMTRADE_TO_IMF_COUNTRY

    rows: list[dict] = []
    for comtrade_country, imf_country in COMTRADE_TO_IMF_COUNTRY.items():
        c_years = set(comtrade_long.loc[comtrade_long["country"] == comtrade_country, "year"])
        i_years = set(imf_long.loc[imf_long["country"] == imf_country, "year"])
        overlap = sorted(c_years & i_years)
        rows.append(
            {
                "country": imf_country,
                "comtrade_year_min": min(c_years) if c_years else None,
                "comtrade_year_max": max(c_years) if c_years else None,
                "imf_year_min": min(i_years) if i_years else None,
                "imf_year_max": max(i_years) if i_years else None,
                "overlap_years": len(overlap),
                "overlap_year_min": overlap[0] if overlap else None,
                "overlap_year_max": overlap[-1] if overlap else None,
            }
        )
    return pd.DataFrame(rows)
