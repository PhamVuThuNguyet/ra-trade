"""Constants for multi-scale Comtrade trade anomaly detection."""

from project_paths import PROJECT_ROOT
from trade_discrepancy.constants import (
    COMTRADE_PARTNER_ISO,
    PARTNER_AUS,
    PARTNER_CHN,
    PARTNER_US,
    PARTNER_WORLD,
)
from trade_influence.constants import PARTNER_DISPLAY, PARTNER_PLOT_COLORS

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "trade_anomaly"
OUTPUT_CSV_DIR = OUTPUT_DIR / "csv"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"

# Annual windows now; monthly extracts can switch FREQUENCY and defaults.
FREQUENCY = "Y"
WINDOWS_YEARS = (1, 3, 5, 7)
STRIDE_YEARS = 1
# Scales that can drive Alert/Critical without needing ultra-short alone.
STRUCTURAL_WINDOWS = (3, 5, 7)
ULTRA_SHORT_WINDOW = 1

BILATERAL_PARTNERS = (PARTNER_AUS, PARTNER_CHN, PARTNER_US)
BILATERAL_PARTNER_ISOS = tuple(COMTRADE_PARTNER_ISO[p] for p in BILATERAL_PARTNERS)
WORLD_PARTNER_ISO = COMTRADE_PARTNER_ISO[PARTNER_WORLD]

FLOWS = ("import", "export")
FLOW_TOTAL = "total"

METRIC_RAW = "raw_usd"
METRIC_STI = "sti"
METRIC_CWTI = "cwti"
METRICS = (METRIC_RAW, METRIC_STI, METRIC_CWTI)

MODEL_NAIVE = "naive"
MODEL_HOLT = "holt"
MODEL_AR1 = "ar1"
MODELS = (MODEL_NAIVE, MODEL_HOLT, MODEL_AR1)

# Trailing residual buffer for w=1 sigma when MAD of a single point is undefined.
NAIVE_SIGMA_LOOKBACK = 3

TIER_NONE = "none"
TIER_WATCH = "watch"
TIER_ALERT = "alert"
TIER_CRITICAL = "critical"
TIERS = (TIER_NONE, TIER_WATCH, TIER_ALERT, TIER_CRITICAL)

Z_WATCH = 2.0
Z_ALERT = 2.5
Z_CRITICAL = 3.0

TYPE_NONE = "none"
TYPE_LEVEL_SHOCK = "level_shock"
TYPE_STRUCTURAL_BREAK = "structural_break"
TYPE_UNCERTAIN = "uncertain"

PERSISTENCE_YEARS = 2

HOLT_ALPHA_GRID = (0.2, 0.4, 0.6, 0.8)
HOLT_BETA_GRID = (0.05, 0.1, 0.2, 0.3)
AR1_MIN_POINTS = 4

# Monthly-ready defaults (unused until freqCode=M extracts are wired).
WINDOWS_MONTHS = (12, 36, 60, 84)
STRIDE_MONTHS = 1

# Manuscript worked-example figures (§8 of the anomaly report).
WORKED_EXAMPLES = (
    {
        "key": "samoa_china_export_raw",
        "series_id": "Samoa|china|export|raw_usd",
        "focus_years": (2015, 2016),
        "filename": "example_samoa_china_export_raw.png",
        "title": "Samoa–China exports (raw USD): structural break 2015–2016",
        "ylabel": "Export value (USD)",
        "value_scale": 1.0,
        "value_scale_label": None,
    },
    {
        "key": "fiji_china_total_sti",
        "series_id": "Fiji|china|total|sti",
        "focus_years": (2014,),
        "filename": "example_fiji_china_total_sti.png",
        "title": "Fiji–China total STI: share-regime shift in 2014",
        "ylabel": "STI (share of total trade)",
        "value_scale": 1.0,
        "value_scale_label": None,
    },
    {
        "key": "tonga_aus_export_raw",
        "series_id": "Tonga|aus|export|raw_usd",
        "focus_years": (2017,),
        "filename": "example_tonga_aus_export_raw.png",
        "title": "Tonga–Australia exports (raw USD): surge in 2017",
        "ylabel": "Export value (USD millions)",
        "value_scale": 1_000_000.0,
        "value_scale_label": "millions",
    },
    {
        "key": "fiji_aus_export_cwti",
        "series_id": "Fiji|aus|export|cwti",
        "focus_years": (2010,),
        "filename": "example_fiji_aus_export_cwti.png",
        "title": "Fiji–Australia export CWTI: Watch-only level shock in 2010",
        "ylabel": "CWTI",
        "value_scale": 1.0,
        "value_scale_label": None,
    },
)

Z_DISPLAY_CAP = 20.0
