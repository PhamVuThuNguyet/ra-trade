"""Run multi-scale Comtrade trade anomaly detection.

Thin wrapper around ``trade_anomaly.pipeline.run_analysis``.
"""

from _bootstrap import add_src_to_path

add_src_to_path()

from trade_anomaly.pipeline import run_analysis


def main() -> None:
    results = run_analysis()
    print("Trade anomaly analysis complete.")
    print(f"Partners: {', '.join(results['partners'])}")
    print(f"Windows (years): {results['windows']}")
    print(
        f"Series: {results['n_series']} unique, "
        f"{results['n_series_years']} series–years, "
        f"{results['n_countries']} countries"
    )
    if results["year_min"] is not None:
        print(f"Years: {results['year_min']}–{results['year_max']}")
    print(f"Scored rows: {results['n_score_rows']}")
    print(f"Attention flags (Watch+): {results['n_alerts']}")
    if not results["by_tier"].empty:
        print("By tier:")
        print(results["by_tier"].to_string(index=False))
    print(f"Plots: {len(results['plots'])}")
    print(f"CSV outputs: {results['csv_dir']}")
    print(f"Plot outputs: {results['plots_dir']}")
    print(f"Outputs written to: {results['output_dir']}")


if __name__ == "__main__":
    main()
