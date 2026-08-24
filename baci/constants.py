"""Constants for CEPII BACI HS02 (version 202601)."""

from pathlib import Path

from comtrade_download.constants import REPORTER_CODES, REPORTER_ISO_BY_CODE
from trade_discrepancy.constants import (
    PARTNER_AUS,
    PARTNER_CHN,
    PARTNER_US,
    PROJECT_ROOT,
    display_comtrade_country,
)

BACI_DIR = PROJECT_ROOT / "data" / "BACI_HS02_V202601"
BACI_VERSION = "202601"
BACI_HS_REVISION = "HS02"
BACI_YEAR_MIN = 2002
BACI_YEAR_MAX = 2024
BACI_YEARS = tuple(range(BACI_YEAR_MIN, BACI_YEAR_MAX + 1))

TRADE_FILE_GLOB = f"BACI_{BACI_HS_REVISION}_Y*_V{BACI_VERSION}.csv"
COUNTRY_CODES_FILENAME = f"country_codes_V{BACI_VERSION}.csv"
PRODUCT_CODES_FILENAME = f"product_codes_{BACI_HS_REVISION}_V{BACI_VERSION}.csv"

COL_YEAR = "t"
COL_EXPORTER = "i"
COL_IMPORTER = "j"
COL_PRODUCT = "k"
COL_VALUE = "v"
COL_QUANTITY = "q"
BACI_COLUMNS = (COL_YEAR, COL_EXPORTER, COL_IMPORTER, COL_PRODUCT, COL_VALUE, COL_QUANTITY)

VALUE_THOUSANDS_TO_USD = 1_000
CHUNK_SIZE = 250_000
HS6_WIDTH = 6
HS2_WIDTH = 2
HS2_COL = "hs2"

CACHE_DIR = PROJECT_ROOT / "outputs" / "baci" / "cache"
PIC_FLOWS_CACHE = CACHE_DIR / "pic_flows.csv"
YEAR_STATS_CACHE = CACHE_DIR / "year_stats.csv"
GLOBAL_HS2_SHARES_CACHE = CACHE_DIR / "global_hs2_shares.csv"

COL_EXPORT_SHARE = "export_share"
COL_IMPORT_SHARE = "import_share"

PIC_CODES = tuple(sorted(int(code) for code in REPORTER_CODES.values()))
PIC_CODE_TO_COMTRADE_NAME = {
    int(code): name for name, code in REPORTER_CODES.items()
}
PIC_CODE_TO_ISO3 = {
    int(code): REPORTER_ISO_BY_CODE[code] for code in REPORTER_CODES.values()
}
PIC_CODE_TO_DISPLAY = {
    code: display_comtrade_country(name)
    for code, name in PIC_CODE_TO_COMTRADE_NAME.items()
}
PIC_DISPLAY_NAMES = tuple(
    PIC_CODE_TO_DISPLAY[code] for code in PIC_CODES
)
PIC_ISO3_BY_DISPLAY = {
    PIC_CODE_TO_DISPLAY[code]: PIC_CODE_TO_ISO3[code] for code in PIC_CODES
}

PARTNER_BACI_CODES = {
    PARTNER_AUS: 36,
    PARTNER_CHN: 156,
    PARTNER_US: 842,
}
PARTNER_CODE_TO_KEY = {code: key for key, code in PARTNER_BACI_CODES.items()}
BILATERAL_PARTNER_CODES = tuple(PARTNER_BACI_CODES.values())
EXPECTED_PARTNER_ISO3 = ("AUS", "CHN", "USA")
