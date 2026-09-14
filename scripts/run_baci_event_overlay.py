"""Overlay the PIC event calendar, Lowy aid, and EM-DAT onto BACI indices."""

from _bootstrap import add_src_to_path

add_src_to_path()

from event_context.pipeline import run_overlay


def main() -> None:
    results = run_overlay()
    print("BACI event overlay complete.")
    print(f"Index rows: {results['n_index_rows']}")
    print(f"Calendar events: {results['n_calendar_events']}")
    print(f"Lowy source: {results['lowy_source']}")
    print(f"EM-DAT source: {results['emdat_source']}")
    print(results["summary"].to_string(index=False))
    print(f"Merged panel: {results['csv_dir']}/indices_baci.csv")
    print(f"Plots: {len(results['plots'])} in {results['plots_dir']}")
    if results["sidecar"]:
        print(f"Sidecar: {results['sidecar']}")


if __name__ == "__main__":
    main()
