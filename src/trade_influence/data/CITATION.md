# HS 2002 → SITC Rev.4 two-digit concordance

**File:** `hs02_hs6_to_sitc4r2.csv`  
**Columns:** `hs6`, `sitc2`, `source`

## Source

Primary correspondence: United Nations Statistics Division, *Standard International Trade Classification, Revision 4* related HS 2002 conversion tables (UNSD commodity classifications).

This extract is **restricted to the 21 essential SITC Rev.4 two-digit divisions** used in the Research Data Explorer (food, agricultural-input, energy, and health security). It is not a full HS–SITC converter for all merchandise trade.

## Matching rule

Lookups try, in order:

1. exact HS 2002 6-digit code
2. HS 4-digit heading (`xxxx` + `00`)
3. HS 2-digit chapter (`xx` + `0000`)

Codes that do not match are **not essential**. Chapter 15 (fats/oils) and 27 (mineral fuels) use 4-digit keys because those chapters split across several SITC divisions.

## Vintage

HS revision: **HS 2002** (BACI HS02 V202601).  
SITC revision: **Rev.4**, two-digit divisions.
