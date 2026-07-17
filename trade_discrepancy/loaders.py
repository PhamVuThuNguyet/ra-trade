from pathlib import Path

import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_DIR,
    COMTRADE_FILE_TO_COUNTRY,
    COMTRADE_TO_IMF_COUNTRY,
    IMF_PATH,
)
from trade_discrepancy.harmonize import aggregate_comtrade, melt_imf, merge_sources


def load_imf(path: Path = IMF_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def load_comtrade_file(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_all_comtrade(
    comtrade_dir: Path = COMTRADE_DIR,
    country_files: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load and concatenate overlapping Pacific Comtrade country files."""
    files = country_files or COMTRADE_FILE_TO_COUNTRY
    frames: list[pd.DataFrame] = []
    for filename in files:
        path = comtrade_dir / filename
        if not path.exists():
            continue
        frames.append(load_comtrade_file(path))
    if not frames:
        raise FileNotFoundError(f"No Comtrade files found in {comtrade_dir}")
    return pd.concat(frames, ignore_index=True)


def build_comparison_table(
    comtrade_dir: Path = COMTRADE_DIR,
    imf_path: Path = IMF_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load, harmonize, and merge both sources into a comparison table."""
    comtrade_raw = load_all_comtrade(comtrade_dir)
    imf_raw = load_imf(imf_path)

    comtrade_long = aggregate_comtrade(comtrade_raw)
    imf_long = melt_imf(imf_raw)
    comparison = merge_sources(comtrade_long, imf_long, COMTRADE_TO_IMF_COUNTRY)
    return comparison, comtrade_long, imf_long


def comtrade_year_ranges(comtrade_dir: Path = COMTRADE_DIR) -> pd.DataFrame:
    """Summarize available Comtrade years per overlapping country."""
    rows: list[dict] = []
    for filename, country in COMTRADE_FILE_TO_COUNTRY.items():
        path = comtrade_dir / filename
        if not path.exists():
            continue
        years = pd.read_csv(path, usecols=["refYear"])["refYear"]
        rows.append(
            {
                "country": country,
                "imf_country": COMTRADE_TO_IMF_COUNTRY[country],
                "year_min": int(years.min()),
                "year_max": int(years.max()),
                "n_years": int(years.nunique()),
            }
        )
    return pd.DataFrame(rows)
