"""Reshape BACI exporter–importer rows into a PIC-as-reporter view."""

from collections.abc import Mapping

import pandas as pd

from baci.constants import (
    COL_EXPORTER,
    COL_IMPORTER,
    COL_PRODUCT,
    COL_QUANTITY,
    COL_VALUE,
    COL_YEAR,
    HS2_COL,
    PIC_CODE_TO_DISPLAY,
    PIC_CODE_TO_ISO3,
    PIC_CODES,
)
from baci.products import product_to_hs2, product_to_hs6

REPORTER_VIEW_COLUMNS = (
    "year",
    "country",
    "iso3",
    "flow",
    "partner_code",
    "hs6",
    HS2_COL,
    "value_thousands_usd",
    "quantity_tons",
)


def _direction_frame(
    flows: pd.DataFrame,
    *,
    pic_col: str,
    partner_col: str,
    flow: str,
    code_to_display: Mapping[int, str],
    code_to_iso3: Mapping[int, str],
) -> pd.DataFrame:
    subset = flows[flows[pic_col].isin(code_to_display)].copy()
    if subset.empty:
        return pd.DataFrame(columns=list(REPORTER_VIEW_COLUMNS))
    subset["year"] = subset[COL_YEAR].astype(int)
    subset["country"] = subset[pic_col].map(code_to_display)
    subset["iso3"] = subset[pic_col].map(code_to_iso3)
    subset["flow"] = flow
    subset["partner_code"] = subset[partner_col].astype(int)
    subset["hs6"] = subset[COL_PRODUCT].map(product_to_hs6)
    subset[HS2_COL] = subset[COL_PRODUCT].map(product_to_hs2)
    subset["value_thousands_usd"] = subset[COL_VALUE].fillna(0.0)
    subset["quantity_tons"] = subset[COL_QUANTITY]
    return subset[list(REPORTER_VIEW_COLUMNS)]


def pic_reporter_view(
    flows: pd.DataFrame,
    *,
    pic_codes: tuple[int, ...] = PIC_CODES,
    code_to_display: Mapping[int, str] | None = None,
    code_to_iso3: Mapping[int, str] | None = None,
) -> pd.DataFrame:
    """
    One row per PIC-facing direction of a BACI flow.

    Exports use the PIC as exporter ``i``; imports use the PIC as importer ``j``.
    Intra-PIC flows therefore appear twice (once in each direction).
    """
    display = dict(code_to_display or PIC_CODE_TO_DISPLAY)
    iso3 = dict(code_to_iso3 or PIC_CODE_TO_ISO3)
    display = {code: display[code] for code in pic_codes if code in display}
    iso3 = {code: iso3[code] for code in pic_codes if code in iso3}
    exports = _direction_frame(
        flows,
        pic_col=COL_EXPORTER,
        partner_col=COL_IMPORTER,
        flow="export",
        code_to_display=display,
        code_to_iso3=iso3,
    )
    imports = _direction_frame(
        flows,
        pic_col=COL_IMPORTER,
        partner_col=COL_EXPORTER,
        flow="import",
        code_to_display=display,
        code_to_iso3=iso3,
    )
    if exports.empty and imports.empty:
        return pd.DataFrame(columns=list(REPORTER_VIEW_COLUMNS))
    return (
        pd.concat([exports, imports], ignore_index=True)
        .sort_values(["country", "year", "flow", "partner_code", "hs6"])
        .reset_index(drop=True)
    )
