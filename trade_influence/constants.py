"""Constants for trade influence indices (STI / CWTI)."""

from pathlib import Path

from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    COMTRADE_TO_IMF_COUNTRY,
    PARTNER_AUS,
    PARTNER_CHN,
    PARTNER_US,
    PARTNER_WORLD,
    PROJECT_ROOT,
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "trade_influence"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"

# Bilateral partners available in the current Comtrade extract (no USA).
COMTRADE_BILATERAL_PARTNERS = (PARTNER_AUS, PARTNER_CHN)
# IMF DOTS includes Australia, China, and the US.
IMF_BILATERAL_PARTNERS = (PARTNER_AUS, PARTNER_CHN, PARTNER_US)

# Backward-compatible alias used by Comtrade-only index code.
BILATERAL_PARTNERS = COMTRADE_BILATERAL_PARTNERS

PARTNER_ISO_TO_KEY = {iso: key for key, iso in COMTRADE_PARTNER_ISO.items()}
BILATERAL_PARTNER_ISO = tuple(COMTRADE_PARTNER_ISO[p] for p in COMTRADE_BILATERAL_PARTNERS)
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

SOURCE_COMTRADE = "comtrade"
SOURCE_IMF = "imf"

SOURCE_DISPLAY = {
    SOURCE_COMTRADE: "Comtrade",
    SOURCE_IMF: "IMF",
}

SOURCE_LINESTYLES = {
    SOURCE_COMTRADE: "-",
    SOURCE_IMF: "--",
}
