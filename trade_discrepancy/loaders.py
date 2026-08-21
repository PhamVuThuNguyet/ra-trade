import csv
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_DIR,
    COMTRADE_FILENAME,
    COMTRADE_TO_IMF_COUNTRY,
    COMTRADE_VALUE_COLUMN_ALIASES,
    COMTRADE_VALUE_COLUMNS,
    IMF_PATH,
    canonical_comtrade_country,
    display_comtrade_country,
)
from trade_discrepancy.harmonize import aggregate_comtrade, melt_imf, merge_sources

COMTRADE_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
EXTRACT_PREFIX = "TradeData_"


def load_imf(path: Path = IMF_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def _decode_comtrade_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in COMTRADE_ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "comtrade",
        raw,
        0,
        1,
        f"Could not decode {path} with {COMTRADE_ENCODINGS}",
    )


def _read_comtrade_rows(path: Path) -> pd.DataFrame:
    """Parse Comtrade CSV, tolerating trailing commas and non-UTF8 bytes."""
    text = _decode_comtrade_text(path)
    reader = csv.reader(text.splitlines())
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValueError(f"Empty Comtrade file: {path}") from exc

    rows: list[list[str]] = []
    for row in reader:
        if not row or all(cell == "" for cell in row):
            continue
        if len(row) == len(header) + 1 and row[-1] == "":
            row = row[:-1]
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        rows.append(row)

    return pd.DataFrame(rows, columns=header)


def normalize_comtrade_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Align value-column names across Comtrade extract formats."""
    rename = {
        source: target
        for source, target in COMTRADE_VALUE_COLUMN_ALIASES.items()
        if source in df.columns and target not in df.columns
    }
    normalized = df.rename(columns=rename)
    numeric_cols = ["refYear", *COMTRADE_VALUE_COLUMNS]
    for col in numeric_cols:
        if col in normalized.columns:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce")
    return normalized


def load_comtrade_file(path: Path) -> pd.DataFrame:
    return normalize_comtrade_schema(_read_comtrade_rows(path))


def comtrade_extract_label(filename: str) -> str:
    """Map TradeData_sitc4_ag3_2000_2024.csv → sitc4_ag3_2000_2024."""
    stem = Path(filename).stem
    if stem.startswith(EXTRACT_PREFIX):
        return stem[len(EXTRACT_PREFIX) :]
    return stem


def resolve_comtrade_paths(
    comtrade_dir: Path = COMTRADE_DIR,
    filenames: Sequence[str] | None = None,
) -> list[Path]:
    """Resolve Comtrade CSV paths (latest Premium extract by default)."""
    names = list(filenames) if filenames is not None else [COMTRADE_FILENAME]
    return [comtrade_dir / name for name in names]


def load_comtrade(
    comtrade_dir: Path = COMTRADE_DIR,
    filenames: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load the latest Comtrade extract, or the named files if provided."""
    frames: list[pd.DataFrame] = []
    for path in resolve_comtrade_paths(comtrade_dir, filenames):
        if not path.exists():
            raise FileNotFoundError(f"Comtrade extract not found: {path}")
        frame = load_comtrade_file(path)
        frame["comtrade_extract"] = comtrade_extract_label(path.name)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def build_comparison_table(
    comtrade_dir: Path = COMTRADE_DIR,
    imf_path: Path = IMF_PATH,
    comtrade_files: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load, harmonize, and merge both sources into a comparison table."""
    comtrade_raw = load_comtrade(comtrade_dir=comtrade_dir, filenames=comtrade_files)
    imf_raw = load_imf(imf_path)
    comtrade_long = aggregate_comtrade(comtrade_raw)
    imf_long = melt_imf(imf_raw)
    comparison = merge_sources(comtrade_long, imf_long, COMTRADE_TO_IMF_COUNTRY)
    return comparison, comtrade_long, imf_long


def comtrade_availability_by_year(comtrade_raw: pd.DataFrame) -> pd.DataFrame:
    """Year-by-year record counts and reporters present in the Comtrade extract."""
    working = comtrade_raw.copy()
    working["year"] = pd.to_numeric(working["refYear"], errors="coerce")
    working["country"] = working["reporterDesc"].map(display_comtrade_country)
    working = working.dropna(subset=["year", "country"])
    working["year"] = working["year"].astype(int)

    rows: list[dict] = []
    for year, group in working.groupby("year", sort=True):
        countries = sorted(group["country"].unique().tolist())
        rows.append(
            {
                "year": int(year),
                "n_records": int(len(group)),
                "n_countries": len(countries),
                "countries": ", ".join(countries),
            }
        )
    return pd.DataFrame(rows)
