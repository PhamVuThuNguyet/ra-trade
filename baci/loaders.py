"""Load CEPII BACI year files, country/product metadata, and PIC-filtered flows."""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from baci.constants import (
    BACI_COLUMNS,
    BACI_DIR,
    BACI_YEARS,
    CACHE_DIR,
    CHUNK_SIZE,
    COL_EXPORTER,
    COL_IMPORTER,
    COL_PRODUCT,
    COL_QUANTITY,
    COL_VALUE,
    COL_YEAR,
    COUNTRY_CODES_FILENAME,
    GLOBAL_HS2_SHARES_CACHE,
    PIC_CODES,
    PIC_FLOWS_CACHE,
    PRODUCT_CODES_FILENAME,
    TRADE_FILE_GLOB,
    YEAR_STATS_CACHE,
)
from baci.global_market import (
    SHARE_COLUMNS,
    chunk_hs2_totals,
    compute_global_market_shares,
    concat_totals,
)

COUNTRY_CODE_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")


def list_year_files(baci_dir: Path = BACI_DIR) -> list[Path]:
    """Year trade-flow CSVs present on disk, oldest year first."""
    return sorted(Path(baci_dir).glob(TRADE_FILE_GLOB))


def load_country_codes(baci_dir: Path = BACI_DIR) -> pd.DataFrame:
    path = Path(baci_dir) / COUNTRY_CODES_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"BACI country codes not found: {path}")
    last_error: Exception | None = None
    for encoding in COUNTRY_CODE_ENCODINGS:
        try:
            frame = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise UnicodeDecodeError(
            "baci",
            b"",
            0,
            1,
            f"Could not decode {path} with {COUNTRY_CODE_ENCODINGS}",
        ) from last_error
    frame["country_code"] = pd.to_numeric(frame["country_code"], errors="coerce")
    return frame.dropna(subset=["country_code"]).astype({"country_code": int})


def load_product_codes(baci_dir: Path = BACI_DIR) -> pd.DataFrame:
    path = Path(baci_dir) / PRODUCT_CODES_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"BACI product codes not found: {path}")
    return pd.read_csv(path, dtype={"code": str})


def _read_trade_chunks(path: Path, chunksize: int):
    return pd.read_csv(
        path,
        usecols=list(BACI_COLUMNS),
        dtype={COL_PRODUCT: str},
        chunksize=chunksize,
    )


def _coerce_trade_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    working = chunk.copy()
    working[COL_YEAR] = pd.to_numeric(working[COL_YEAR], errors="coerce")
    working[COL_EXPORTER] = pd.to_numeric(working[COL_EXPORTER], errors="coerce")
    working[COL_IMPORTER] = pd.to_numeric(working[COL_IMPORTER], errors="coerce")
    working[COL_VALUE] = pd.to_numeric(working[COL_VALUE], errors="coerce")
    working[COL_QUANTITY] = pd.to_numeric(working[COL_QUANTITY], errors="coerce")
    return working


def _year_from_filename(path: Path) -> int | None:
    try:
        year_token = path.stem.split("_Y", 1)[1].split("_", 1)[0]
        return int(year_token)
    except (IndexError, ValueError):
        return None


def _empty_pic_flows() -> pd.DataFrame:
    return pd.DataFrame(columns=list(BACI_COLUMNS))


def _empty_year_stats() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "year",
            "n_records",
            "n_pic_records",
            "n_exporters",
            "n_importers",
            "n_products",
            "value_thousands_usd_sum",
            "qty_missing_n",
            "qty_missing_share",
        ]
    )


def scan_year_file(
    path: Path,
    *,
    pic_codes: Sequence[int] = PIC_CODES,
    chunksize: int = CHUNK_SIZE,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Filter one year file to PIC flows; collect year stats and HS-2 global shares."""
    pic_set = set(pic_codes)
    pic_chunks: list[pd.DataFrame] = []
    world_parts: list[pd.DataFrame] = []
    export_parts: list[pd.DataFrame] = []
    import_parts: list[pd.DataFrame] = []
    n_records = 0
    n_pic = 0
    exporters: set[int] = set()
    importers: set[int] = set()
    products: set[str] = set()
    qty_missing_n = 0
    value_sum = 0.0
    year = _year_from_filename(path)

    for raw in _read_trade_chunks(path, chunksize):
        chunk = _coerce_trade_chunk(raw)
        n_records += len(chunk)
        qty_missing_n += int(chunk[COL_QUANTITY].isna().sum())
        value_sum += float(chunk[COL_VALUE].fillna(0).sum())
        exporters.update(chunk[COL_EXPORTER].dropna().astype(int).unique().tolist())
        importers.update(chunk[COL_IMPORTER].dropna().astype(int).unique().tolist())
        products.update(chunk[COL_PRODUCT].dropna().astype(str).unique().tolist())
        if year is None and chunk[COL_YEAR].notna().any():
            year = int(chunk[COL_YEAR].dropna().iloc[0])
        mask = chunk[COL_EXPORTER].isin(pic_set) | chunk[COL_IMPORTER].isin(pic_set)
        pic = chunk.loc[mask]
        n_pic += len(pic)
        if not pic.empty:
            pic_chunks.append(pic)
        world, exports, imports = chunk_hs2_totals(chunk)
        world_parts.append(world)
        export_parts.append(exports)
        import_parts.append(imports)

    stats = {
        "year": year,
        "n_records": n_records,
        "n_pic_records": n_pic,
        "n_exporters": len(exporters),
        "n_importers": len(importers),
        "n_products": len(products),
        "value_thousands_usd_sum": value_sum,
        "qty_missing_n": qty_missing_n,
        "qty_missing_share": (qty_missing_n / n_records) if n_records else 0.0,
    }
    pic_flows = (
        pd.concat(pic_chunks, ignore_index=True) if pic_chunks else _empty_pic_flows()
    )
    shares = compute_global_market_shares(
        concat_totals(world_parts, "world_value"),
        concat_totals(export_parts, "partner_exports"),
        concat_totals(import_parts, "partner_imports"),
    )
    return pic_flows, stats, shares


def scan_baci(
    baci_dir: Path = BACI_DIR,
    *,
    pic_codes: Sequence[int] = PIC_CODES,
    chunksize: int = CHUNK_SIZE,
    years: Sequence[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read every year file; return PIC flows, year stats, and global HS-2 shares."""
    wanted = set(years) if years is not None else set(BACI_YEARS)
    pic_frames: list[pd.DataFrame] = []
    stats_rows: list[dict] = []
    share_frames: list[pd.DataFrame] = []
    for path in list_year_files(baci_dir):
        file_year = _year_from_filename(path)
        if file_year is not None and file_year not in wanted:
            continue
        pic_flows, stats, shares = scan_year_file(
            path, pic_codes=pic_codes, chunksize=chunksize
        )
        stats_rows.append(stats)
        if not pic_flows.empty:
            pic_frames.append(pic_flows)
        if not shares.empty:
            share_frames.append(shares)

    year_stats = (
        pd.DataFrame(stats_rows).sort_values("year").reset_index(drop=True)
        if stats_rows
        else _empty_year_stats()
    )
    flows = (
        pd.concat(pic_frames, ignore_index=True) if pic_frames else _empty_pic_flows()
    )
    if not flows.empty:
        flows = flows[flows[COL_EXPORTER] != flows[COL_IMPORTER]].reset_index(drop=True)
    global_shares = (
        pd.concat(share_frames, ignore_index=True).sort_values(
            ["year", "hs2", "partner"]
        ).reset_index(drop=True)
        if share_frames
        else pd.DataFrame(columns=list(SHARE_COLUMNS))
    )
    return flows, year_stats, global_shares


def _write_cache(
    pic_flows: pd.DataFrame,
    year_stats: pd.DataFrame,
    global_shares: pd.DataFrame,
    *,
    flows_path: Path,
    stats_path: Path,
    shares_path: Path,
) -> None:
    flows_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    shares_path.parent.mkdir(parents=True, exist_ok=True)
    pic_flows.to_csv(flows_path, index=False)
    year_stats.to_csv(stats_path, index=False)
    global_shares.to_csv(shares_path, index=False)


def _read_cache(
    flows_path: Path, stats_path: Path, shares_path: Path
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pic_flows = pd.read_csv(flows_path, dtype={COL_PRODUCT: str})
    year_stats = pd.read_csv(stats_path)
    global_shares = pd.read_csv(shares_path, dtype={"hs2": str})
    global_shares["hs2"] = (
        global_shares["hs2"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    )
    return pic_flows, year_stats, global_shares


def load_baci_extract(
    baci_dir: Path = BACI_DIR,
    *,
    pic_codes: Sequence[int] = PIC_CODES,
    chunksize: int = CHUNK_SIZE,
    years: Sequence[int] | None = None,
    use_cache: bool = True,
    cache_dir: Path = CACHE_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """PIC flows, year stats, and partner global HS-2 market shares."""
    flows_path = Path(cache_dir) / PIC_FLOWS_CACHE.name
    stats_path = Path(cache_dir) / YEAR_STATS_CACHE.name
    shares_path = Path(cache_dir) / GLOBAL_HS2_SHARES_CACHE.name
    if (
        use_cache
        and flows_path.exists()
        and stats_path.exists()
        and shares_path.exists()
    ):
        return _read_cache(flows_path, stats_path, shares_path)

    pic_flows, year_stats, global_shares = scan_baci(
        baci_dir, pic_codes=pic_codes, chunksize=chunksize, years=years
    )
    if use_cache:
        _write_cache(
            pic_flows,
            year_stats,
            global_shares,
            flows_path=flows_path,
            stats_path=stats_path,
            shares_path=shares_path,
        )
    return pic_flows, year_stats, global_shares


def load_pic_flows(
    baci_dir: Path = BACI_DIR,
    *,
    pic_codes: Sequence[int] = PIC_CODES,
    chunksize: int = CHUNK_SIZE,
    years: Sequence[int] | None = None,
    use_cache: bool = True,
    cache_dir: Path = CACHE_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PIC-related BACI flows and per-year dataset stats.

    Cache defaults to ``outputs/baci/cache`` so characteristics and influence
    pipelines can share one scan of the large year files.
    """
    pic_flows, year_stats, _shares = load_baci_extract(
        baci_dir,
        pic_codes=pic_codes,
        chunksize=chunksize,
        years=years,
        use_cache=use_cache,
        cache_dir=cache_dir,
    )
    return pic_flows, year_stats
