"""Labelled mock services panel for the Explorer Tool only."""

from explorer_catalog.constants import SOURCE_BACI, SOURCE_COMTRADE

COUNTRIES = ("Fiji", "Samoa", "Tonga")
PARTNERS = ("aus", "china", "us")
YEARS = tuple(range(2015, 2023))
ALL_SERVICE_CATEGORIES = ("Travel", "Transport")
ESSENTIAL_SERVICE_CATEGORIES = ("Health", "Education")
PRODUCT_GROUP_ESSENTIAL = "essential_commodities"

_BASE_ALL = {
    "Fiji": {"Travel": 1.2e6, "Transport": 4.5e5},
    "Samoa": {"Travel": 3.2e5, "Transport": 1.1e5},
    "Tonga": {"Travel": 2.1e5, "Transport": 8.0e4},
}
_BASE_ESSENTIAL = {
    "Fiji": {"Health": 8.4e5, "Education": 3.1e5},
    "Samoa": {"Health": 2.2e5, "Education": 9.5e4},
    "Tonga": {"Health": 1.6e5, "Education": 7.2e4},
}
_PARTNER_WEIGHT = {"aus": 1.0, "china": 0.72, "us": 0.55}


def mock_service_rows(product_group_id: str = "all_products") -> list[dict]:
    """PIC × partner × year × category mock USD values (not study output)."""
    if product_group_id == PRODUCT_GROUP_ESSENTIAL:
        categories = ESSENTIAL_SERVICE_CATEGORIES
        base = _BASE_ESSENTIAL
    else:
        categories = ALL_SERVICE_CATEGORIES
        base = _BASE_ALL
    rows: list[dict] = []
    for country in COUNTRIES:
        for year in YEARS:
            drift = 1 + 0.03 * (year - 2015)
            for partner in PARTNERS:
                for category in categories:
                    shock = 0.62 if year in {2020, 2021} and category in {"Travel", "Education"} else 1.0
                    value = base[country][category] * _PARTNER_WEIGHT[partner] * drift * shock
                    rows.append(
                        {
                            "country": country,
                            "year": year,
                            "partner": partner,
                            "service_category": category,
                            "value_usd": round(value, 2),
                        }
                    )
    return rows


def mock_service_table(source_id: str, product_group_id: str = "all_products") -> dict:
    return {
        "source_id": source_id,
        "data_type_id": "services",
        "product_group_id": product_group_id,
        "provenance": "mock",
        "vintage": None,
        "columns": ["country", "year", "partner", "service_category", "value_usd"],
        "rows": mock_service_rows(product_group_id),
    }


def mock_service_tables() -> list[dict]:
    return [
        mock_service_table(SOURCE_COMTRADE),
        mock_service_table(SOURCE_BACI),
        mock_service_table(SOURCE_COMTRADE, PRODUCT_GROUP_ESSENTIAL),
        mock_service_table(SOURCE_BACI, PRODUCT_GROUP_ESSENTIAL),
    ]
