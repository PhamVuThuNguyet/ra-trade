"""Orchestrate Pacific SITC Rev.4 AG3 Comtrade extracts."""

from pathlib import Path

import pandas as pd

from comtrade_download.auth import load_subscription_keys
from comtrade_download.client import complete_async_extract, fetch_final_data, fetch_final_data_async
from comtrade_download.constants import ENV_PATH, ComtradeDownloadError
from comtrade_download.prepare import save_extract


def download_pacific_sitc4_ag3(
    output_path: Path | None = None,
    env_path: Path = ENV_PATH,
    *,
    batch_id: str | None = None,
    use_async: bool = True,
) -> tuple[Path, pd.DataFrame]:
    keys = load_subscription_keys(env_path)
    frame: pd.DataFrame | None = None
    last_error: Exception | None = None
    if batch_id:
        frame = complete_async_extract(keys[0], batch_id)
    elif use_async:
        for key in keys:
            try:
                frame = fetch_final_data_async(key)
                break
            except ComtradeDownloadError as exc:
                last_error = exc
        if frame is None:
            print(f"Async extract failed ({last_error}); falling back to sync calls.", flush=True)
            frame = fetch_final_data(keys)
    else:
        frame = fetch_final_data(keys)
    path = save_extract(frame, output_path)
    return path, frame
