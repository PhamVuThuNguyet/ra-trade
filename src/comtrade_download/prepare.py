"""Normalize Comtrade API payloads into loader-compatible tables."""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from comtrade_download.constants import (
    OUTPUT_DIR,
    OUTPUT_FILENAME,
    PARTNER_CODES,
    PARTNER_ISO_BY_CODE,
    REPORTER_CODES,
    REPORTER_ISO_BY_CODE,
)


def camel_case_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {
        column: column[0].lower() + column[1:]
        for column in frame.columns
        if column[:1].isupper()
    }
    return frame.rename(columns=renamed)


def _map_codes(series: pd.Series, lookup: Mapping[str, str]) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).map(lookup)


def _missing_or_blank(frame: pd.DataFrame, column: str) -> bool:
    return column not in frame.columns or frame[column].isna().all()


def enrich_geography(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    reporter_desc = {code: name for name, code in REPORTER_CODES.items()}
    partner_desc = {code: name for name, code in PARTNER_CODES.items()}
    if "reporterCode" in working.columns:
        if _missing_or_blank(working, "reporterDesc"):
            working["reporterDesc"] = _map_codes(working["reporterCode"], reporter_desc)
        if _missing_or_blank(working, "reporterISO"):
            working["reporterISO"] = _map_codes(working["reporterCode"], REPORTER_ISO_BY_CODE)
    if "partnerCode" in working.columns:
        if _missing_or_blank(working, "partnerDesc"):
            working["partnerDesc"] = _map_codes(working["partnerCode"], partner_desc)
        if _missing_or_blank(working, "partnerISO"):
            working["partnerISO"] = _map_codes(working["partnerCode"], PARTNER_ISO_BY_CODE)
    return working


def prepare_extract_frame(frame: pd.DataFrame) -> pd.DataFrame:
    working = enrich_geography(camel_case_columns(frame))
    if "cmdCode" in working.columns:
        working["cmdCode"] = (
            working["cmdCode"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
        )
    return working


def read_extract_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            inner_name = archive.namelist()[0]
            with archive.open(inner_name) as handle:
                frame = pd.read_csv(handle, sep="\t", encoding="utf-8-sig")
    else:
        compression = "gzip" if path.name.endswith(".gz") else None
        frame = pd.read_csv(path, compression=compression)
    return prepare_extract_frame(frame)


def save_extract(frame: pd.DataFrame, path: Path | None = None) -> Path:
    output_path = path or (OUTPUT_DIR / OUTPUT_FILENAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_extract_frame(frame).to_csv(output_path, index=False)
    return output_path
