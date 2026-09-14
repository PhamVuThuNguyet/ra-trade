"""Call UN Comtrade Premium sync and async data APIs."""

from __future__ import annotations

import os
import time
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlparse

import comtradeapicall
import pandas as pd
import urllib3

from comtrade_download.constants import (
    ASYNC_POLL_SECONDS,
    OUTPUT_DIR,
    PERIODS,
    REPORTER_CODES,
    REQUEST_PAUSE_SECONDS,
    ComtradeDownloadError,
)
from comtrade_download.prepare import read_extract_file
from comtrade_download.query import async_request_kwargs, final_data_kwargs


def _call_final_data(subscription_key: str, **kwargs: object) -> pd.DataFrame:
    frame = comtradeapicall.getFinalData(subscription_key, **kwargs)
    if frame is None:
        raise ComtradeDownloadError(
            "Comtrade API returned no payload; check the subscription key and query."
        )
    return frame


def _fetch_period(
    subscription_key: str,
    period: str,
    *,
    pause_seconds: float,
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for index, reporter_code in enumerate(REPORTER_CODES.values()):
        part = _call_final_data(
            subscription_key,
            **final_data_kwargs(period, reporter_code=reporter_code),
        )
        if not part.empty:
            parts.append(part)
        if pause_seconds and index < len(REPORTER_CODES) - 1:
            time.sleep(pause_seconds)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def fetch_final_data(
    subscription_keys: str | Sequence[str],
    *,
    periods: Sequence[str] = PERIODS,
    pause_seconds: float = REQUEST_PAUSE_SECONDS,
) -> pd.DataFrame:
    keys = (subscription_keys,) if isinstance(subscription_keys, str) else tuple(subscription_keys)
    last_error: Exception | None = None
    for key in keys:
        try:
            frames: list[pd.DataFrame] = []
            for index, period in enumerate(periods):
                print(f"Fetching {period} by reporter...", flush=True)
                frame = _fetch_period(key, period, pause_seconds=pause_seconds)
                if not frame.empty:
                    frames.append(frame)
                if pause_seconds and index < len(periods) - 1:
                    time.sleep(pause_seconds)
            if frames:
                return pd.concat(frames, ignore_index=True)
            return pd.DataFrame()
        except ComtradeDownloadError as exc:
            last_error = exc
            continue
    raise ComtradeDownloadError("All Comtrade subscription keys failed.") from last_error


def submit_async_extract(subscription_key: str, periods: Sequence[str] = PERIODS) -> str:
    result = comtradeapicall.submitAsyncFinalDataRequest(
        subscription_key,
        **async_request_kwargs(periods),
    )
    if not result or result.get("error") or "requestId" not in result:
        raise ComtradeDownloadError(f"Async submit failed: {result}")
    request_id = result["requestId"]
    print(f"Submitted async extract {request_id}", flush=True)
    return request_id


def poll_async_extract(
    subscription_key: str,
    batch_id: str,
    *,
    poll_seconds: float = ASYNC_POLL_SECONDS,
) -> pd.Series:
    status = ""
    row: pd.Series | None = None
    while status not in {"Completed", "Error"}:
        status_df = comtradeapicall.checkAsyncDataRequest(
            subscription_key,
            batchId=batch_id,
        )
        if status_df is None or status_df.empty:
            raise ComtradeDownloadError(f"No async status for batch {batch_id}")
        row = status_df.iloc[0]
        status = str(row["status"])
        print(f"Async batch {batch_id}: {status}", flush=True)
        if status in {"Completed", "Error"}:
            break
        if poll_seconds:
            time.sleep(poll_seconds)
    if row is None or status != "Completed":
        raise ComtradeDownloadError(f"Async extract {batch_id} failed: {row}")
    return row


def download_async_file(uri: str, directory: Path) -> Path:
    filename = os.path.basename(urlparse(uri).path) or "comtrade-async.csv"
    path = directory / filename
    directory.mkdir(parents=True, exist_ok=True)
    http = urllib3.PoolManager()
    with path.open("wb") as handle:
        response = http.request("GET", uri, preload_content=False)
        try:
            if response.status != 200:
                raise ComtradeDownloadError(
                    f"Failed to download async file ({response.status}): {uri}"
                )
            for chunk in response.stream(65536):
                handle.write(chunk)
        finally:
            response.release_conn()
    return path


def complete_async_extract(
    subscription_key: str,
    batch_id: str,
    *,
    download_dir: Path = OUTPUT_DIR,
    poll_seconds: float = ASYNC_POLL_SECONDS,
) -> pd.DataFrame:
    row = poll_async_extract(
        subscription_key,
        batch_id,
        poll_seconds=poll_seconds,
    )
    uri = row.get("uri")
    if pd.isna(uri) or not str(uri).startswith("http"):
        raise ComtradeDownloadError(f"Async extract {batch_id} completed without a file URI")
    path = download_async_file(str(uri), download_dir)
    print(f"Downloaded async file {path.name}", flush=True)
    return read_extract_file(path)


def fetch_final_data_async(
    subscription_key: str,
    *,
    periods: Sequence[str] = PERIODS,
    download_dir: Path = OUTPUT_DIR,
    poll_seconds: float = ASYNC_POLL_SECONDS,
) -> pd.DataFrame:
    batch_id = submit_async_extract(subscription_key, periods)
    return complete_async_extract(
        subscription_key,
        batch_id,
        download_dir=download_dir,
        poll_seconds=poll_seconds,
    )
