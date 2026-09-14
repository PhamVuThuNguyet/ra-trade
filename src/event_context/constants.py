"""Paths and codes for PIC event, Lowy aid, and EM-DAT overlays."""

from pathlib import Path

from baci.constants import PIC_ISO3_BY_DISPLAY
from project_paths import PROJECT_ROOT
from trade_discrepancy.constants import (
    PARTNER_AUS,
    PARTNER_CHN,
    PARTNER_US,
)
from trade_influence.constants import BACI_OUTPUT_CSV_DIR

PACKAGE_DIR = Path(__file__).resolve().parent
CALENDAR_PATH = PACKAGE_DIR / "pic_event_calendar.csv"

DATA_DIR = PROJECT_ROOT / "data" / "event_context"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "baci_events"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
INDICES_BACI_PATH = BACI_OUTPUT_CSV_DIR / "indices_baci.csv"
INDICES_EVENTS_SIDECAR = BACI_OUTPUT_CSV_DIR / "indices_baci_events.csv"

ALL_COUNTRIES = "*"
ALL_PARTNERS = "*"
BACI_YEAR_MIN = 2002
BACI_YEAR_MAX = 2024

PDH_BASE_URL = "https://stats-sdmx-disseminate.pacificdata.org/rest"
PDH_AGENCY = "SPC"
PDH_DATAFLOW = "DF_PAM"
PDH_USER_AGENT = "research-assistant/0.1 (academic PIC trade overlay)"
LOWY_RAW_CSV = DATA_DIR / "df_pam_raw.csv"
LOWY_AGGREGATE_DONORS = ("_T", "DONOR_BIL", "DONOR_MUL", "DONOR_CSP", "DONOR_PCS")

EMDAT_HDX_URL = (
    "https://data.humdata.org/dataset/74163686-a029-4e27-8fbf-c5bfcd13f953/"
    "resource/c5ce40d6-07b1-4f36-955a-d6196436ff6b/"
    "download/emdat-country-profiles_2026_09_02.xlsx"
)
EMDAT_RAW_XLSX = DATA_DIR / "emdat_country_profiles.xlsx"

ISO2_TO_DISPLAY = {
    "CK": "Cook Islands",
    "FJ": "Fiji",
    "KI": "Kiribati",
    "MH": "Marshall Islands",
    "FM": "Micronesia",
    "NR": "Nauru",
    "NU": "Niue",
    "PW": "Palau",
    "PG": "Papua New Guinea",
    "WS": "Samoa",
    "SB": "Solomon Islands",
    "TO": "Tonga",
    "TV": "Tuvalu",
    "VU": "Vanuatu",
}
ISO3_TO_DISPLAY = {iso3: name for name, iso3 in PIC_ISO3_BY_DISPLAY.items()}
DISPLAY_TO_ISO3 = dict(PIC_ISO3_BY_DISPLAY)

DONOR_CODE_TO_PARTNER = {
    "AU": PARTNER_AUS,
    "AUS": PARTNER_AUS,
    "CN": PARTNER_CHN,
    "CHN": PARTNER_CHN,
    "US": PARTNER_US,
    "USA": PARTNER_US,
}
DONOR_NAME_TO_PARTNER = {
    "australia": PARTNER_AUS,
    "china": PARTNER_CHN,
    "people's republic of china": PARTNER_CHN,
    "united states": PARTNER_US,
    "united states of america": PARTNER_US,
}

FLAG_TYPES = (
    "gfc",
    "covid",
    "pacer_plus",
    "diplomatic_switch",
    "ramsi",
    "step_up",
    "compact_renewal",
    "security_pact",
    "coup",
    "unrest",
    "disaster",
    "commodity",
    "sanctions",
    "engagement",
    "processing_centre",
    "wto_accession",
)

CORE_OUTPUT_FILES = (
    "event_calendar.csv",
    "lowy_aid_by_partner.csv",
    "emdat_by_country_year.csv",
    "indices_baci.csv",
    "coverage_summary.csv",
)
