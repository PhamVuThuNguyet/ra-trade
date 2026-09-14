"""Characterize CEPII BACI HS02 coverage and the Pacific Island slice.

Thin wrapper around ``baci_characteristics.pipeline.run_analysis``.
"""

from _bootstrap import add_src_to_path

add_src_to_path()

from baci_characteristics.pipeline import run_analysis


def main() -> None:
    results = run_analysis()
    print("BACI HS02 characterization complete.")
    print(f"Full-dataset records: {results['n_records_full']:,}")
    print(f"PIC-view records: {results['n_records_pic_view']:,}")
    print(
        f"Reporters: {results['n_reporters_observed']} of "
        f"{results['n_reporters_requested']} requested"
    )
    if results["year_min"] is not None:
        print(
            f"Years with PIC data: {results['year_min']}–{results['year_max']} "
            f"({results['n_years_observed']} years)"
        )
    print(f"Incomplete AUS/CHN/USA cells: {results['n_partner_gaps']}")
    print("Overview:")
    print(results["overview"].to_string(index=False))
    print(f"CSV outputs: {results['csv_dir']}")


if __name__ == "__main__":
    main()
