"""Download helper for cached remote files."""

from pathlib import Path

import requests

from event_context.constants import PDH_USER_AGENT

CHUNK_SIZE = 65_536


def download_file(
    url: str,
    dest: Path,
    *,
    timeout: int = 120,
    user_agent: str = PDH_USER_AGENT,
) -> Path:
    """Stream ``url`` to ``dest``, replacing the file only after a full download."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    headers = {"User-Agent": user_agent}
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    handle.write(chunk)
    tmp.replace(dest)
    return dest


def get_text(
    url: str,
    *,
    timeout: int = 120,
    user_agent: str = PDH_USER_AGENT,
) -> str:
    """GET a URL and return the response body as text."""
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text
