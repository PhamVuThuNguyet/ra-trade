"""Explorer catalog constants. Display names match trade_influence reports."""

from project_paths import PROJECT_ROOT
from batis_services.constants import OUTPUT_CSV_DIR as BATIS_OUTPUT_CSV_DIR
from batis_services.constants import SOURCE_BATIS, VINTAGE as BATIS_VINTAGE
from trade_influence.constants import (
    BACI_OUTPUT_CSV_DIR,
    ESSENTIAL_SITC2,
    INDEX_CWE,
    INDEX_CWE_ESSENTIAL,
    INDEX_CWI,
    INDEX_CWI_ESSENTIAL,
    INDEX_DISPLAY,
    INDEX_EXPORT,
    INDEX_IMPORT,
    OUTPUT_CSV_DIR,
    PARTNER_DISPLAY,
    PARTNER_PLOT_COLORS,
    SOURCE_BACI,
    SOURCE_COMTRADE,
    SOURCE_DISPLAY,
)

BACI_VINTAGE = "BACI HS02 V202601"
COMTRADE_VINTAGE = "Comtrade SITC Rev.4"
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "explorer-tool" / "public" / "data" / "catalog.json"
GOODS_TRADE_INDEX_IDS = (
    INDEX_IMPORT,
    INDEX_EXPORT,
    INDEX_CWI,
    INDEX_CWE,
    INDEX_CWI_ESSENTIAL,
    INDEX_CWE_ESSENTIAL,
)
UI_FLAGS = {
    "partner_filter": False,
    "index_toggles": False,
    "goods_trade_index_ids": list(GOODS_TRADE_INDEX_IDS),
}

ESSENTIAL_DIVISIONS = (
    {"code": "00", "description": "Live animals other than animals of division 03", "purpose": "food_security"},
    {"code": "01", "description": "Meat and meat preparations", "purpose": "food_security"},
    {"code": "02", "description": "Dairy products and birds' eggs", "purpose": "food_security"},
    {"code": "03", "description": "Fish (not marine mammals), crustaceans, molluscs and aquatic invertebrates, and preparations thereof", "purpose": "food_security"},
    {"code": "04", "description": "Cereals and cereal preparations", "purpose": "food_security"},
    {"code": "05", "description": "Vegetables and fruit", "purpose": "food_security"},
    {"code": "06", "description": "Sugars, sugar preparations and honey", "purpose": "food_security"},
    {"code": "07", "description": "Coffee, tea, cocoa, spices, and manufactures thereof", "purpose": "food_security"},
    {"code": "08", "description": "Feeding stuff for animals (not including unmilled cereals)", "purpose": "food_security"},
    {"code": "09", "description": "Miscellaneous edible products and preparations", "purpose": "food_security"},
    {"code": "27", "description": "Crude fertilizers, other than those of division 56, and crude minerals (excluding coal, petroleum and precious stones)", "purpose": "agricultural_input_security"},
    {"code": "32", "description": "Coal, coke and briquettes", "purpose": "energy_security"},
    {"code": "33", "description": "Petroleum, petroleum products and related materials", "purpose": "energy_security"},
    {"code": "34", "description": "Gas, natural and manufactured", "purpose": "energy_security"},
    {"code": "35", "description": "Electric current", "purpose": "energy_security"},
    {"code": "41", "description": "Animal oils and fats", "purpose": "food_security"},
    {"code": "42", "description": "Fixed vegetable fats and oils, crude, refined or fractionated", "purpose": "food_security"},
    {"code": "43", "description": "Animal or vegetable fats and oils, processed; waxes of animal or vegetable origin", "purpose": "food_security"},
    {"code": "54", "description": "Medicinal and pharmaceutical products", "purpose": "health_security"},
    {"code": "56", "description": "Fertilizers (other than those of group 272)", "purpose": "agricultural_input_security"},
)

assert tuple(d["code"] for d in ESSENTIAL_DIVISIONS) == ESSENTIAL_SITC2
