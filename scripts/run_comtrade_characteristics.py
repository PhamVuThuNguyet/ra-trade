"""Characterize the Pacific SITC Rev.4 AG3 Comtrade API extract.

Thin wrapper around ``comtrade_characteristics.pipeline.run_analysis``.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from comtrade_characteristics.pipeline import run_analysis


def main() -> None:
    results = run_analysis()
    print("Comtrade API extract characterization complete.")
    print(f"Records: {results['n_records']:,}")
    print(
        f"Reporters: {results['n_reporters_observed']} of "
        f"{results['n_reporters_requested']} requested"
    )
    if results["year_min"] is not None:
        print(
            f"Years with data: {results['year_min']}–{results['year_max']} "
            f"({results['n_years_observed']} years)"
        )
    print(f"Incomplete partner cells: {results['n_partner_gaps']}")
    print("Overview:")
    print(results["overview"].to_string(index=False))
    print("Availability by year:")
    print(results["availability"].to_string(index=False))
    print(f"CSV outputs: {results['csv_dir']}")


if __name__ == "__main__":
    main()
