"""Run Comtrade I/E/CWI/CWE and IMF I/E analysis; export time-series plots.

Thin wrapper around ``trade_influence.pipeline.run_analysis``.
"""

from _bootstrap import add_src_to_path

add_src_to_path()

from trade_influence.pipeline import run_analysis


def main() -> None:
    results = run_analysis()
    print("Trade influence analysis complete.")
    print(f"Partners: {', '.join(results['partners'])}")
    print(
        f"Comtrade I/E/CWI/CWE: {results['n_index_observations']} obs, "
        f"{results['n_countries']} countries"
    )
    print(
        f"IMF I/E: {results['n_imf_observations']} obs, "
        f"{results['n_imf_countries']} countries"
    )
    if results["year_min"] is not None:
        print(f"Comtrade years: {results['year_min']}–{results['year_max']}")
    if results["imf_year_min"] is not None:
        print(f"IMF years: {results['imf_year_min']}–{results['imf_year_max']}")
    print("Headlines by source/partner:")
    print(results["by_source_partner"].to_string(index=False))
    print(f"Plots: {len(results['plots'])}")
    print(f"CSV outputs: {results['csv_dir']}")
    print(f"Plot outputs: {results['plots_dir']}")
    print(f"Outputs written to: {results['output_dir']}")


if __name__ == "__main__":
    main()
