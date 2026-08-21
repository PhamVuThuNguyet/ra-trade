from pathlib import Path

from comtrade_download.constants import (
    OUTPUT_DIR as COMTRADE_DIR,
    OUTPUT_FILENAME as COMTRADE_FILENAME,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMTRADE_PATH = COMTRADE_DIR / COMTRADE_FILENAME
IMF_PATH = PROJECT_ROOT / "data" / "IMF data" / "IMF_Pacific_DOTS.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "trade_discrepancy"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"

COMTRADE_VALUE_COLUMN_ALIASES = {
    "cifvalue": "cifvalue__US__",
    "fobvalue": "fobvalue__US__",
    "primaryValue": "primaryValue__US__",
}

COMTRADE_VALUE_COLUMNS = (
    "cifvalue__US__",
    "fobvalue__US__",
    "primaryValue__US__",
)

COMTRADE_SCHEMA_KEYS = (
    "reporterDesc",
    "refYear",
    "flowCode",
    "partnerISO",
    "cmdCode",
    "classificationCode",
    "freqCode",
    "cifvalue__US__",
    "fobvalue__US__",
    "primaryValue__US__",
    "comtrade_extract",
)

USD_TO_MILLIONS = 1_000_000
DISCREPANCY_TOLERANCE_PCT = 5.0
LARGEST_GAPS_N = 10

COMTRADE_TO_IMF_COUNTRY = {
    "Fiji": "Fiji, Republic of",
    "Kiribati": "Kiribati",
    "Palau": "Palau, Republic of",
    "Papua New Guinea": "Papua New Guinea",
    "Samoa": "Samoa",
    "Solomon Islands": "Solomon Islands",
    "Tonga": "Tonga",
}

PARTNER_WORLD = "world"
PARTNER_AUS = "aus"
PARTNER_CHN = "china"
PARTNER_US = "us"
PARTNER_ORDER = (PARTNER_WORLD, PARTNER_AUS, PARTNER_CHN, PARTNER_US)

IMF_PARTNER_COLUMNS = {
    PARTNER_AUS: ("exports_aus", "imports_aus"),
    PARTNER_CHN: ("exports_china", "imports_china"),
    PARTNER_US: ("exports_us", "imports_us"),
    PARTNER_WORLD: ("exports_world", "imports_world"),
}

IMF_SCHEMA_KEYS = (
    "country",
    "time_period",
    "exports_world",
    "imports_world",
    "exports_aus",
    "imports_aus",
    "exports_china",
    "imports_china",
    "exports_us",
    "imports_us",
)

COMTRADE_PARTNER_ISO = {
    PARTNER_AUS: "AUS",
    PARTNER_CHN: "CHN",
    PARTNER_US: "USA",
    PARTNER_WORLD: "W00",
}

COMTRADE_REPORTER_ALIASES = {
    "Solomon Isds": "Solomon Islands",
}

COMTRADE_COUNTRY_DISPLAY = {
    "Cook Isds": "Cook Islands",
    "FS Micronesia": "Micronesia",
    "Marshall Isds": "Marshall Islands",
    "Solomon Isds": "Solomon Islands",
    "Solomon Islands": "Solomon Islands",
}

FLOW_EXPORT = "export"
FLOW_IMPORT = "import"
FLOW_ORDER = (FLOW_IMPORT, FLOW_EXPORT)
FLOW_CODE_IMPORT = "M"
FLOW_CODE_EXPORT = "X"

VALUATION_STANDARD = "standard"
VALUATION_PRIMARY = "primary"
VALUATION_CIF_FOB_ONLY = "cif_fob_only"

COVERAGE_SUMMARY_COLUMNS = (
    "country",
    "comtrade_year_min",
    "comtrade_year_max",
    "imf_year_min",
    "imf_year_max",
    "overlap_years",
    "overlap_year_min",
    "overlap_year_max",
)

IMF_TO_COMTRADE_COUNTRY = {
    imf_name: comtrade_name
    for comtrade_name, imf_name in COMTRADE_TO_IMF_COUNTRY.items()
}


def canonical_comtrade_country(reporter_desc: str) -> str:
    return COMTRADE_REPORTER_ALIASES.get(reporter_desc, reporter_desc)


def display_comtrade_country(reporter_desc: str) -> str:
    canonical = canonical_comtrade_country(reporter_desc)
    return COMTRADE_COUNTRY_DISPLAY.get(canonical, canonical)
