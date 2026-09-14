"""HS product-code helpers for BACI."""

import pandas as pd

from baci.constants import HS2_WIDTH, HS6_WIDTH


def product_to_hs6(code) -> str:
    """Pad a BACI product code to HS 6-digit, preserving leading zeros."""
    if pd.isna(code):
        raise ValueError("product code is missing")
    text = str(code).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        raise ValueError(f"Cannot derive HS-6 from product code={code!r}")
    return digits.zfill(HS6_WIDTH)[:HS6_WIDTH]


def product_to_hs2(code) -> str:
    """Map an HS 6-digit product code to its 2-digit chapter."""
    return product_to_hs6(code)[:HS2_WIDTH]


def product_series_to_hs2(codes: pd.Series) -> pd.Series:
    """Vectorized HS-2 chapter codes from a product-code column."""
    return codes.astype(str).str.zfill(HS6_WIDTH).str[:HS2_WIDTH]
