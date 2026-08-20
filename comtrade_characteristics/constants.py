"""Constants for characterizing the Pacific Comtrade API extract."""

from comtrade_download.constants import (
    OUTPUT_DIR as EXTRACT_DIR,
    OUTPUT_FILENAME,
    PERIOD_END_YEAR,
    PERIOD_START_YEAR,
    REPORTER_CODES,
    REPORTER_ISO_BY_CODE,
)
from trade_discrepancy.constants import PROJECT_ROOT, display_comtrade_country

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "comtrade_characteristics"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"

FLOW_LABELS = {"M": "import", "X": "export"}
EXPECTED_PARTNERS = ("AUS", "CHN", "USA", "W00")

REQUESTED_YEARS = tuple(range(PERIOD_START_YEAR, PERIOD_END_YEAR + 1))
REQUESTED_REPORTERS = tuple(display_comtrade_country(name) for name in REPORTER_CODES)
REPORTER_ISO_BY_DISPLAY = {
    display_comtrade_country(name): REPORTER_ISO_BY_CODE[code]
    for name, code in REPORTER_CODES.items()
}
