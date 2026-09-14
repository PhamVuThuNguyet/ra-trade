"""Download the Pacific SITC Rev.4 AG3 Comtrade extract for 2000–2024."""

import sys

from _bootstrap import add_src_to_path

add_src_to_path()

from comtrade_download import download_pacific_sitc4_ag3


def main() -> None:
    batch_id = sys.argv[1] if len(sys.argv) > 1 else None
    path, frame = download_pacific_sitc4_ag3(batch_id=batch_id)
    years = sorted(_to_years(frame))
    reporters = _unique(frame, "reporterDesc")
    partners = _unique(frame, "partnerDesc")
    print(f"Downloaded {len(frame):,} rows to {path}")
    print(f"Years: {years[0]}-{years[-1]}" if years else "Years: none")
    print(f"Reporters ({len(reporters)}): {', '.join(reporters)}")
    print(f"Partners ({len(partners)}): {'; '.join(partners)}")


def _to_years(frame) -> list[int]:
    years = frame["refYear"] if "refYear" in frame.columns else frame.get("period")
    if years is None:
        return []
    return [int(year) for year in years.dropna().unique()]


def _unique(frame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    return sorted(frame[column].dropna().astype(str).unique())


if __name__ == "__main__":
    main()
