from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd
import pytest

from comtrade_download.auth import load_subscription_keys, parse_env_file
from comtrade_download.client import complete_async_extract, fetch_final_data
from comtrade_download.constants import (
    BREAKDOWN_MODE,
    CLASSIFICATION_CODE,
    CMD_CODE,
    CUSTOMS_CODE,
    FLOW_CODE,
    FREQ_CODE,
    MAX_RECORDS,
    MOT_CODE,
    OUTPUT_DIR,
    OUTPUT_FILENAME,
    PARTNER2_CODE,
    PARTNER_CODES,
    PERIODS,
    REPORTER_CODES,
    TYPE_CODE,
    ComtradeDownloadError,
)
from comtrade_download.pipeline import download_pacific_sitc4_ag3
from comtrade_download.prepare import read_extract_file, save_extract
from comtrade_download.query import async_request_kwargs, final_data_kwargs, joined_codes


def test_parse_env_file_reads_keys(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("COMTRADE_PRIM_KEY=abc123\nCOMTRADE_SEC_KEY='xyz789'\n", encoding="utf-8")
    values = parse_env_file(env_path)
    assert values["COMTRADE_PRIM_KEY"] == "abc123"
    assert values["COMTRADE_SEC_KEY"] == "xyz789"


def test_load_subscription_keys_prefers_environ_over_file(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("COMTRADE_PRIM_KEY=from-file\n", encoding="utf-8")
    keys = load_subscription_keys(env_path, environ={"COMTRADE_PRIM_KEY": "from-env"})
    assert keys == ("from-env",)


def test_load_subscription_keys_requires_a_key(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER=1\n", encoding="utf-8")
    with pytest.raises(ComtradeDownloadError, match="Missing COMTRADE_PRIM_KEY"):
        load_subscription_keys(env_path, environ={})


def test_final_data_kwargs_match_screenshot_filter():
    kwargs = final_data_kwargs("2024")
    assert kwargs["typeCode"] == TYPE_CODE == "C"
    assert kwargs["freqCode"] == FREQ_CODE == "A"
    assert kwargs["clCode"] == CLASSIFICATION_CODE == "S4"
    assert kwargs["cmdCode"] == CMD_CODE == "AG3"
    assert kwargs["period"] == "2024"
    assert kwargs["flowCode"] == FLOW_CODE == "M,X"
    assert kwargs["partner2Code"] == PARTNER2_CODE == "0"
    assert kwargs["customsCode"] == CUSTOMS_CODE == "C00"
    assert kwargs["motCode"] == MOT_CODE == "0"
    assert kwargs["breakdownMode"] == BREAKDOWN_MODE == "plus"
    assert kwargs["aggregateBy"] is None
    assert kwargs["includeDesc"] is True
    assert kwargs["maxRecords"] == MAX_RECORDS
    assert kwargs["reporterCode"] == joined_codes(REPORTER_CODES)
    assert kwargs["partnerCode"] == joined_codes(PARTNER_CODES)
    assert kwargs["partnerCode"].endswith(",0")
    assert "842" in kwargs["partnerCode"]
    assert set(PERIODS) == {str(year) for year in range(2018, 2025)}
    assert list(REPORTER_CODES) == [
        "Cook Isds",
        "Fiji",
        "FS Micronesia",
        "Kiribati",
        "Marshall Isds",
        "Nauru",
        "Niue",
        "Palau",
        "Papua New Guinea",
        "Samoa",
        "Solomon Isds",
        "Tonga",
        "Tuvalu",
        "Vanuatu",
    ]


def test_async_request_kwargs_cover_full_screenshot_query():
    kwargs = async_request_kwargs()
    assert kwargs["period"] == ",".join(PERIODS)
    assert kwargs["reporterCode"] == joined_codes(REPORTER_CODES)
    assert kwargs["partnerCode"] == joined_codes(PARTNER_CODES)
    assert kwargs["cmdCode"] == "AG3"
    assert kwargs["clCode"] == "S4"
    assert kwargs["breakdownMode"] == "plus"
    assert "maxRecords" not in kwargs


def test_fetch_final_data_queries_each_reporter_and_concatenates_periods():
    def fake_get(_key, **kwargs):
        return pd.DataFrame(
            [
                {
                    "refYear": int(kwargs["period"]),
                    "reporterCode": kwargs["reporterCode"],
                }
            ]
        )

    with patch("comtrade_download.client.comtradeapicall.getFinalData", side_effect=fake_get):
        frame = fetch_final_data("key", periods=("2018", "2019"), pause_seconds=0)

    assert set(frame["refYear"]) == {2018, 2019}
    assert set(frame["reporterCode"]) == set(REPORTER_CODES.values())
    assert len(frame) == len(REPORTER_CODES) * 2


def test_fetch_final_data_falls_back_to_secondary_key():
    calls: list[str] = []

    def fake_get(key, **_kwargs):
        calls.append(key)
        if key == "primary":
            return None
        return pd.DataFrame([{"refYear": 2018, "reporterDesc": "Tonga"}])

    with patch("comtrade_download.client.comtradeapicall.getFinalData", side_effect=fake_get):
        frame = fetch_final_data(("primary", "secondary"), periods=("2018",), pause_seconds=0)

    assert calls[0] == "primary"
    assert "secondary" in calls
    assert frame.iloc[0]["reporterDesc"] == "Tonga"


def test_complete_async_extract_polls_until_completed(tmp_path: Path):
    csv_path = tmp_path / "async.csv"
    csv_path.write_text("refYear,reporterDesc\n2022,Fiji\n", encoding="utf-8")
    statuses = [
        pd.DataFrame([{"status": "Submitted", "uri": None}]),
        pd.DataFrame([{"status": "Completed", "uri": "https://example.test/async.csv"}]),
    ]

    with (
        patch(
            "comtrade_download.client.comtradeapicall.checkAsyncDataRequest",
            side_effect=statuses,
        ),
        patch(
            "comtrade_download.client.download_async_file",
            return_value=csv_path,
        ),
    ):
        frame = complete_async_extract("key", "batch-1", download_dir=tmp_path, poll_seconds=0)

    assert list(frame["reporterDesc"]) == ["Fiji"]


def test_read_extract_file_normalizes_async_zip_tsv(tmp_path: Path):
    zip_path = tmp_path / "batch.zip"
    body = "\ufeffTypeCode\tRefYear\tReporterCode\tPartnerCode\tFlowCode\tCmdCode\nC\t2022\t242\t36\tM\t1\n"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("batch.txt", body)

    frame = read_extract_file(zip_path)
    assert list(frame["refYear"]) == [2022]
    assert list(frame["reporterDesc"]) == ["Fiji"]
    assert list(frame["partnerISO"]) == ["AUS"]
    assert list(frame["partnerDesc"]) == ["Australia"]
    assert list(frame["cmdCode"]) == ["001"]


def test_save_extract_and_download_use_output_dir(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("COMTRADE_PRIM_KEY=abc\n", encoding="utf-8")
    output_path = tmp_path / OUTPUT_FILENAME
    sample = pd.DataFrame([{"refYear": 2020, "reporterDesc": "Fiji"}])

    saved = save_extract(sample, output_path)
    assert saved == output_path
    assert pd.read_csv(saved).iloc[0]["reporterDesc"] == "Fiji"
    assert OUTPUT_DIR.name == "NEW COMTRADE data"

    with patch(
        "comtrade_download.pipeline.fetch_final_data_async",
        return_value=sample,
    ):
        path, frame = download_pacific_sitc4_ag3(output_path=output_path, env_path=env_path)
    assert path == output_path
    assert len(frame) == 1
