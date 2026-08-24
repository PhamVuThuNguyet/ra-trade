"""Constants for trade influence indices (I, E, CWI, CWE)."""

from pathlib import Path

from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    COMTRADE_TO_IMF_COUNTRY,
    PARTNER_AUS,
    PARTNER_CHN,
    PARTNER_US,
    PARTNER_WORLD,
    PROJECT_ROOT,
    display_comtrade_country,
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "trade_influence"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"
BACI_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "baci_influence"
BACI_OUTPUT_CSV_DIR = BACI_OUTPUT_DIR / "csv"
BACI_OUTPUT_PLOTS_DIR = BACI_OUTPUT_DIR / "plots"

# Comtrade AG3 codes are SITC Rev.4 groups; pad to this width then take 2 digits.
SITC_GROUP_WIDTH = 3
COMMODITY_COL = "sitc2"
COMMODITY_COL_HS2 = "hs2"

BILATERAL_PARTNERS = (PARTNER_AUS, PARTNER_CHN, PARTNER_US)

PARTNER_ISO_TO_KEY = {iso: key for key, iso in COMTRADE_PARTNER_ISO.items()}
BILATERAL_PARTNER_ISO = tuple(COMTRADE_PARTNER_ISO[p] for p in BILATERAL_PARTNERS)
WORLD_PARTNER_ISO = COMTRADE_PARTNER_ISO[PARTNER_WORLD]

IMF_TO_COMTRADE_COUNTRY = {imf: ct for ct, imf in COMTRADE_TO_IMF_COUNTRY.items()}

PARTNER_DISPLAY = {
    PARTNER_AUS: "Australia",
    PARTNER_CHN: "China",
    PARTNER_US: "United States",
}

PARTNER_PLOT_COLORS = {
    PARTNER_AUS: "#1f77b4",
    PARTNER_CHN: "#d62728",
    PARTNER_US: "#2ca02c",
}

INDEX_IMPORT = "import_index"
INDEX_EXPORT = "export_index"
INDEX_CWI = "cwi"
INDEX_CWE = "cwe"

INDEX_DISPLAY = {
    INDEX_IMPORT: "I",
    INDEX_EXPORT: "E",
    INDEX_CWI: "CWI",
    INDEX_CWE: "CWE",
}

FLOW_TO_SHARE_INDEX = {
    "import": INDEX_IMPORT,
    "export": INDEX_EXPORT,
}

FLOW_TO_CW_INDEX = {
    "import": INDEX_CWI,
    "export": INDEX_CWE,
}

# CWI: partner j's share of world exports of c (iw). CWE: j's share of world imports (ew).
FLOW_TO_GLOBAL_SHARE_COL = {
    "import": "export_share",
    "export": "import_share",
}

SOURCE_COMTRADE = "comtrade"
SOURCE_IMF = "imf"
SOURCE_BACI = "baci"

SOURCE_DISPLAY = {
    SOURCE_COMTRADE: "Comtrade",
    SOURCE_IMF: "IMF",
    SOURCE_BACI: "BACI",
}

SOURCE_LINESTYLES = {
    SOURCE_COMTRADE: "-",
    SOURCE_IMF: "--",
}

IMF_COUNTRY_DISPLAY = {
    "Marshall Islands, Republic of the": "Marshall Islands",
    "Micronesia, Federated States of": "Micronesia",
    "Nauru, Republic of": "Nauru",
}


def display_country(name: str) -> str:
    """Short labels for Comtrade reporter names and unmapped IMF DOTS names."""
    return IMF_COUNTRY_DISPLAY.get(name, display_comtrade_country(name))
