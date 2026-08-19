"""Constants for UN Comtrade Premium API downloads."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "data" / "NEW COMTRADE data"

PRIMARY_KEY_NAME = "COMTRADE_PRIM_KEY"
SECONDARY_KEY_NAME = "COMTRADE_SEC_KEY"

TYPE_CODE = "C"
FREQ_CODE = "A"
CLASSIFICATION_CODE = "S4"
CMD_CODE = "AG3"
FLOW_CODE = "M,X"
PARTNER2_CODE = "0"
CUSTOMS_CODE = "C00"
MOT_CODE = "0"
BREAKDOWN_MODE = "plus"
MAX_RECORDS = 250_000
REQUEST_PAUSE_SECONDS = 1.0
ASYNC_POLL_SECONDS = 15.0

PERIODS = ("2018", "2019", "2020", "2021", "2022", "2023", "2024")

REPORTER_CODES = {
    "Cook Isds": "184",
    "Fiji": "242",
    "FS Micronesia": "583",
    "Kiribati": "296",
    "Marshall Isds": "584",
    "Nauru": "520",
    "Niue": "570",
    "Palau": "585",
    "Papua New Guinea": "598",
    "Samoa": "882",
    "Solomon Isds": "90",
    "Tonga": "776",
    "Tuvalu": "798",
    "Vanuatu": "548",
}

PARTNER_CODES = {
    "Australia": "36",
    "China": "156",
    "USA, Puerto Rico and US Virgin Islands": "842",
    "World": "0",
}

OUTPUT_FILENAME = "TradeData_sitc4_ag3_2018_2024.csv"

REPORTER_ISO_BY_CODE = {
    "184": "COK",
    "242": "FJI",
    "583": "FSM",
    "296": "KIR",
    "584": "MHL",
    "520": "NRU",
    "570": "NIU",
    "585": "PLW",
    "598": "PNG",
    "882": "WSM",
    "90": "SLB",
    "776": "TON",
    "798": "TUV",
    "548": "VUT",
}

PARTNER_ISO_BY_CODE = {
    "36": "AUS",
    "156": "CHN",
    "842": "USA",
    "0": "W00",
}

ASYNC_KWARG_NAMES = (
    "typeCode",
    "freqCode",
    "clCode",
    "period",
    "reporterCode",
    "cmdCode",
    "flowCode",
    "partnerCode",
    "partner2Code",
    "customsCode",
    "motCode",
    "aggregateBy",
    "breakdownMode",
)


class ComtradeDownloadError(RuntimeError):
    """Raised when the Comtrade Premium extract cannot be downloaded."""
