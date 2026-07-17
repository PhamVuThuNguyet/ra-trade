"""Run UN Comtrade vs IMF discrepancy analysis and export results.

This CLI is a thin wrapper around ``trade_discrepancy.pipeline.run_analysis``,
which is also used by ``notebooks/trade_discrepancy_analysis.ipynb``.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from trade_discrepancy.pipeline import run_analysis


def main() -> None:
    results = run_analysis()
    print("Trade discrepancy analysis complete.")
    print(f"Analysis dimensions: {', '.join(results['analysis_dimensions'])}")
    print(f"Comparable observations: {results['n_comparable_observations']}")
    print(f"World-total observations: {results['n_world_observations']}")
    print(
        f"Median world symmetric % diff: "
        f"{results['median_world_symmetric_pct_diff']:.2f}%"
    )
    print(f"Share within 5% (world): {results['share_world_within_5pct']:.1%}")
    print("Partner headlines:")
    print(results["by_partner"].to_string(index=False))
    print(f"Plots: {len(results['plots'])}")
    print(f"CSV outputs: {results['csv_dir']}")
    print(f"Plot outputs: {results['plots_dir']}")
    print(f"Outputs written to: {results['output_dir']}")


if __name__ == "__main__":
    main()
