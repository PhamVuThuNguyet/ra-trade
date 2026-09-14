"""Run BACI HS-2 I/E/CWI/CWE analysis; export time-series plots.

Thin wrapper around ``trade_influence.baci_pipeline.run_baci_analysis``.
"""

from _bootstrap import add_src_to_path

add_src_to_path()

from trade_influence.baci_pipeline import run_baci_analysis


def main() -> None:
    results = run_baci_analysis()
    print("BACI trade influence analysis complete.")
    print(f"Partners: {', '.join(results['partners'])}")
    print(
        f"BACI I/E/CWI/CWE: {results['n_index_observations']} obs, "
        f"{results['n_countries']} countries"
    )
    if results["year_min"] is not None:
        print(f"BACI years: {results['year_min']}–{results['year_max']}")
    print("Headlines by partner:")
    print(results["by_partner"].to_string(index=False))
    print(f"Plots: {len(results['plots'])}")
    print(f"CSV outputs: {results['csv_dir']}")
    print(f"Plot outputs: {results['plots_dir']}")
    print(f"Outputs written to: {results['output_dir']}")


if __name__ == "__main__":
    main()
