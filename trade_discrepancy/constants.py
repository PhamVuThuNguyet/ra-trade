from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMTRADE_DIR = PROJECT_ROOT / "data" / "COMMTRADE data"
IMF_PATH = PROJECT_ROOT / "data" / "IMF data" / "IMF_Pacific_DOTS.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "trade_discrepancy"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"

USD_TO_MILLIONS = 1_000_000
DISCREPANCY_TOLERANCE_PCT = 5.0

COMTRADE_TO_IMF_COUNTRY = {
    "Fiji": "Fiji, Republic of",
    "Kiribati": "Kiribati",
    "Palau": "Palau, Republic of",
    "Papua New Guinea": "Papua New Guinea",
    "Samoa": "Samoa",
    "Solomon Islands": "Solomon Islands",
    "Tonga": "Tonga",
}

COMTRADE_FILE_TO_COUNTRY = {
    "Fiji_panel2.csv": "Fiji",
    "Kiribati_panel2.csv": "Kiribati",
    "Palau_panel2.csv": "Palau",
    "Papua_New_Guinea_panel2.csv": "Papua New Guinea",
    "Samoa_panel2.csv": "Samoa",
    "Solomon_Isds_panel2.csv": "Solomon Islands",
    "Tonga_panel2.csv": "Tonga",
}

PARTNER_WORLD = "world"
PARTNER_AUS = "aus"
PARTNER_CHN = "china"
PARTNER_US = "us"

IMF_PARTNER_COLUMNS = {
  PARTNER_AUS: ("exports_aus", "imports_aus"),
  PARTNER_CHN: ("exports_china", "imports_china"),
  PARTNER_US: ("exports_us", "imports_us"),
  PARTNER_WORLD: ("exports_world", "imports_world"),
}

COMTRADE_PARTNER_ISO = {
    PARTNER_AUS: "AUS",
    PARTNER_CHN: "CHN",
    PARTNER_WORLD: "W00",
}

COMTRADE_REPORTER_ALIASES = {
    "Solomon Isds": "Solomon Islands",
}


def canonical_comtrade_country(reporter_desc: str) -> str:
    return COMTRADE_REPORTER_ALIASES.get(reporter_desc, reporter_desc)


FLOW_EXPORT = "export"
FLOW_IMPORT = "import"

VALUATION_STANDARD = "standard"
VALUATION_PRIMARY = "primary"
VALUATION_CIF_FOB_ONLY = "cif_fob_only"

VALUATION_METHODS = (VALUATION_STANDARD, VALUATION_PRIMARY, VALUATION_CIF_FOB_ONLY)

HS2_WORLD_PARTNER_ISO = "W00"
PARTNER_GAP_TOLERANCE_PCT = 1.0
PC_SHARE_TOLERANCE_PCT = 0.5
