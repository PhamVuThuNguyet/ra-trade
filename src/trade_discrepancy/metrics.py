import numpy as np
import pandas as pd

from trade_discrepancy.constants import (
    DISCREPANCY_TOLERANCE_PCT,
    LARGEST_GAPS_N,
    PARTNER_ORDER,
    PARTNER_WORLD,
)


def add_discrepancy_metrics(comparison: pd.DataFrame) -> pd.DataFrame:
    """Compute absolute, symmetric-percentage, and log-ratio discrepancies."""
    result = comparison.copy()
    result["abs_diff_musd"] = result["imf_value_musd"] - result["comtrade_value_musd"]
    denominator = result["imf_value_musd"].abs() + result["comtrade_value_musd"].abs()
    result["symmetric_pct_diff"] = np.where(
        denominator > 0,
        200 * result["abs_diff_musd"] / denominator,
        np.nan,
    )
    result["log_ratio"] = np.where(
        (result["imf_value_musd"] > 0) & (result["comtrade_value_musd"] > 0),
        np.log(result["imf_value_musd"] / result["comtrade_value_musd"]),
        np.nan,
    )
    result["within_tolerance"] = (
        result["symmetric_pct_diff"].abs() <= DISCREPANCY_TOLERANCE_PCT
    )
    return result


def _order_by_partner(frame: pd.DataFrame) -> pd.DataFrame:
    rank = {partner: index for index, partner in enumerate(PARTNER_ORDER)}
    return frame.sort_values(
        "partner", key=lambda series: series.map(lambda partner: rank.get(partner, 99))
    ).reset_index(drop=True)


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


def partner_headline_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate headline SymDiff% stats by partner."""
    rows: list[dict] = []
    for partner, group in metrics.groupby("partner", sort=False):
        rows.append(
            {
                "partner": partner,
                "n_observations": len(group),
                "median_symmetric_pct_diff": group["symmetric_pct_diff"].median(),
                "mean_abs_symmetric_pct_diff": group["symmetric_pct_diff"].abs().mean(),
                "share_within_tolerance": group["within_tolerance"].mean(),
            }
        )
    return _order_by_partner(pd.DataFrame(rows))


def largest_world_discrepancies(
    metrics: pd.DataFrame,
    n: int = LARGEST_GAPS_N,
) -> pd.DataFrame:
    """Return the n largest absolute SymDiff% observations for world totals."""
    cols = [
        "country_comtrade",
        "year",
        "flow",
        "comtrade_value_musd",
        "imf_value_musd",
        "abs_diff_musd",
        "symmetric_pct_diff",
        "within_tolerance",
    ]
    world = metrics[metrics["partner"] == PARTNER_WORLD].copy()
    world["abs_symmetric_pct"] = world["symmetric_pct_diff"].abs()
    available = [col for col in cols if col in world.columns]
    return (
        world.sort_values("abs_symmetric_pct", ascending=False)[available]
        .head(n)
        .reset_index(drop=True)
    )
