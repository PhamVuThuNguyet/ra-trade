# Characteristics of the Pacific Island UN Comtrade API Extract

**Request:** SITC Rev. 4, three-digit aggregates (`AG3`); annual; imports and exports; 14 Pacific Island reporters; partners Australia, China, USA (M49 `842`), and World; calendar years 2000–2024  
**Retrieval:** UN Comtrade Premium Institutional Pro asynchronous job

---

## 1. Headline findings

| Requested | Observed |
| --- | --- |
| 25 years (2000–2024) | **17 years** with at least one row (**2008–2024**). **2000–2007 are empty.** |
| 14 Pacific Island reporters | **8** reporters with at least one row; **6** requested reporters have **no rows** |
| 14 × 25 = 350 reporter–years | **70** cells with data (**20%** of the requested grid) |
| Partners AUS, CHN, USA, W00 | All four present in every year that has data |
| Flows M and X | Both present; imports are 72% of rows |

The file contains **79,200** commodity-level records, **261** distinct SITC AG3 codes, classification `S4`, frequency `A`, customs `C00`, and mode of transport `0`.

Fiji is the only reporter with an unbroken 2008–2024 series. Peak geographic coverage is six reporters in 2017–2018. 2024 currently contains only Fiji and Samoa.

---

## 2. Years

No SITC Rev. 4 AG3 rows are published for these fourteen reporters in **2000–2007**. Data begin in 2008. Record volume peaks in 2017 (6,433 rows, six reporters) and is thinnest after 2008 in 2024 (2,547 rows, two reporters), consistent with lagged publication.

**Table 1.** Records and reporters by year (requested window 2000–2024)

| Year | Records | Reporters with data | Reporters |
| --- | ---: | ---: | --- |
| 2000–2007 | 0 | 0 | — |
| 2008 | 2,341 | 3 | Cook Islands, Fiji, Tonga |
| 2009 | 3,204 | 3 | Fiji, Samoa, Tonga |
| 2010 | 3,317 | 3 | Fiji, Samoa, Tonga |
| 2011 | 4,735 | 4 | Fiji, Papua New Guinea, Samoa, Tonga |
| 2012 | 4,933 | 4 | Fiji, Papua New Guinea, Samoa, Tonga |
| 2013 | 3,643 | 3 | Fiji, Samoa, Tonga |
| 2014 | 5,490 | 5 | Fiji, Kiribati, Palau, Samoa, Tonga |
| 2015 | 5,302 | 5 | Fiji, Kiribati, Palau, Samoa, Solomon Islands |
| 2016 | 5,397 | 5 | Fiji, Kiribati, Palau, Samoa, Solomon Islands |
| 2017 | 6,433 | 6 | Fiji, Kiribati, Palau, Samoa, Solomon Islands, Tonga |
| 2018 | 6,265 | 6 | Fiji, Kiribati, Palau, Samoa, Solomon Islands, Tonga |
| 2019 | 5,186 | 4 | Fiji, Papua New Guinea, Samoa, Tonga |
| 2020 | 4,659 | 4 | Fiji, Kiribati, Papua New Guinea, Tonga |
| 2021 | 5,706 | 5 | Fiji, Kiribati, Papua New Guinea, Samoa, Tonga |
| 2022 | 5,005 | 4 | Fiji, Papua New Guinea, Samoa, Tonga |
| 2023 | 5,037 | 4 | Fiji, Papua New Guinea, Samoa, Tonga |
| 2024 | 2,547 | 2 | Fiji, Samoa |

Full CSV: `outputs/comtrade_characteristics/csv/availability_by_year.csv`.

---

## 3. Reporters

Fourteen economies were requested (download report, Table 3). Eight appear in the extract. Six have no published SITC Rev. 4 AG3 rows in 2000–2024: **Micronesia, Marshall Islands, Nauru, Niue, Tuvalu, Vanuatu**.

**Table 2.** Requested reporters versus the published extract

| Reporter | ISO3 | Observed | Records | Years with data | Share of 2000–2024 | Span | Flows |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Cook Islands | COK | Yes | 17 | 1 | 4% | 2008 | X only |
| Fiji | FJI | Yes | 24,832 | 17 | 68% | 2008–2024 | M, X |
| Micronesia | FSM | No | 0 | 0 | 0% | — | — |
| Kiribati | KIR | Yes | 5,861 | 7 | 28% | 2014–2021 | M, X |
| Marshall Islands | MHL | No | 0 | 0 | 0% | — | — |
| Nauru | NRU | No | 0 | 0 | 0% | — | — |
| Niue | NIU | No | 0 | 0 | 0% | — | — |
| Palau | PLW | Yes | 4,542 | 5 | 20% | 2014–2018 | M, X |
| Papua New Guinea | PNG | Yes | 9,860 | 7 | 28% | 2011–2023 | M, X |
| Samoa | WSM | Yes | 15,689 | 15 | 60% | 2009–2024 | M, X |
| Solomon Islands | SLB | Yes | 3,861 | 4 | 16% | 2015–2018 | M, X |
| Tonga | TON | Yes | 14,538 | 14 | 56% | 2008–2023 | M, X |
| Tuvalu | TUV | No | 0 | 0 | 0% | — | — |
| Vanuatu | VUT | No | 0 | 0 | 0% | — | — |

Fiji accounts for 31% of all rows. Cook Islands contributes 17 export rows in 2008 and nothing else. Intra-span gaps (years inside a reporter’s min–max with no rows) are:

| Reporter | Years present | Gaps inside the span |
| --- | --- | --- |
| Kiribati | 2014–2018, 2020–2021 | 2019 |
| Papua New Guinea | 2011–2012, 2019–2023 | 2013–2018 |
| Samoa | 2009–2019, 2021–2024 | 2020 |
| Tonga | 2008–2014, 2017–2023 | 2015–2016 |

---

## 4. Reporter × year coverage

**Table 3.** Presence on the requested 14 × 25 grid. A mark means at least one commodity-level row. Years **2000–2007** are empty for every reporter and are omitted here. Long-form panel: `outputs/comtrade_characteristics/csv/reporter_year_panel.csv`.

| Reporter | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Cook Islands | • | | | | | | | | | | | | | | | | |
| Fiji | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • |
| Micronesia | | | | | | | | | | | | | | | | | |
| Kiribati | | | | | | | • | • | • | • | • | | • | • | | | |
| Marshall Islands | | | | | | | | | | | | | | | | | |
| Nauru | | | | | | | | | | | | | | | | | |
| Niue | | | | | | | | | | | | | | | | | |
| Palau | | | | | | | • | • | • | • | • | | | | | | |
| Papua New Guinea | | | | • | • | | | | | | | • | • | • | • | • | |
| Samoa | | • | • | • | • | • | • | • | • | • | • | • | | • | • | • | • |
| Solomon Islands | | | | | | | | • | • | • | • | | | | | | |
| Tonga | • | • | • | • | • | • | • | | | • | • | • | • | • | • | • | |
| Tuvalu | | | | | | | | | | | | | | | | | |
| Vanuatu | | | | | | | | | | | | | | | | | |

---

## 5. Partners and flows

The four requested partners (`AUS`, `CHN`, `USA`, `W00`) appear in every year from 2008 through 2024. World rows outnumber each bilateral partner, as expected for an AG3 plus-mode extract (every commodity that exists for any partner also exists, typically, in the World total). Imports dominate the row count (57,038 import rows, 22,162 export rows). Cook Islands is export-only.

Of 139 country–year–flow cells, **seven** do not contain every requested partner. All seven are **export** cells missing a single bilateral partner (World remains present):

| Reporter | Year | Flow | Partners present | Missing |
| --- | --- | --- | --- | --- |
| Kiribati | 2014, 2016, 2018, 2021 | export | AUS, USA, W00 | CHN |
| Palau | 2016 | export | CHN, USA, W00 | AUS |
| Palau | 2017 | export | AUS, USA, W00 | CHN |
| Tonga | 2022 | export | AUS, USA, W00 | CHN |

These are sparse-export gaps (no AG3 row for that partner), not missing World totals. CSV: `partner_gaps.csv`.

---

## 6. Commodities and valuation fields

- **Classification:** `S4` (SITC Rev. 4), `cmdCode` stored as three-digit strings (`001`–`971`).
- **Distinct AG3 codes:** 261 in the file as a whole; PNG uses all 261, Fiji 260, Cook Islands only 11.
- **`primaryValue`:** populated on every row.
- **CIF / FOB:** follow the usual Comtrade pattern and should not be treated as missing at random.

**Table 4.** Value-field completeness by flow

| Flow | Rows | CIF non-null | FOB non-null | Primary non-null |
| --- | ---: | ---: | ---: | ---: |
| Import (M) | 57,038 | 94.6% | 28.0% | 100% |
| Export (X) | 22,162 | 24.5% | 100% | 100% |

Downstream loaders that use CIF for imports and FOB for exports, with primary as fallback, therefore have a complete primary series and a near-complete standard valuation series on the matching flow.

Quantity (`qty`) is non-null on 83.6% of rows and net weight on 82.6%; gross weight is thinner (53.5%). Those fields are not used by the current discrepancy, influence, or anomaly pipelines.
