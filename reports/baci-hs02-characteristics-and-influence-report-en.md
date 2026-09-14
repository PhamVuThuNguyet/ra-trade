# BACI HS02: Data Characteristics and Trade Influence Indices

**Source:** CEPII BACI, Harmonized System 2002 revision, release **202601** (22 January 2026)  
**Local files:** `data/BACI_HS02_V202601`  
**Documentation:** [CEPII BACI webpage](https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html)

This report characterizes the new BACI extract and computes Pacific Island **I / E / I^Y / E^Y / CWI / CWE** influence indices on it. World totals for I and E are **summed from all bilateral partners** (BACI has no World aggregate). Commodity weights use **HS 2-digit chapters**. CWI and CWE multiply each chapter by the partner’s **global market share** and by the PIC’s **imports/GDP** (CWI) or **exports/GDP** (CWE).

---

## 1. Objectives

> Evaluate Pacific Island Countries’ (PICs) **vulnerability to foreign influence through trade** with Australia, China, and the United States.

| Index | Full name | Role |
| ----- | --------- | ---- |
| **I** | Import index | Partner share of total imports |
| **E** | Export index | Partner share of total exports |
| **I^Y** | Import exposure | Bilateral imports / GDP |
| **E^Y** | Export exposure | Bilateral exports / GDP |
| **CWI** | Commodity Weighted Import index | Partner concentration in important import chapters, × world export share × \(M/Y\) |
| **CWE** | Commodity Weighted Export index | Partner concentration in important export chapters, × world import share × \(X/Y\) |

---

## 2. What BACI is

BACI is an annual bilateral trade database at **HS 6-digit** product level. Each flow is a unique exporter–importer–product–year cell with a **reconciled FOB value** (thousand current USD) and quantity (metric tons). Only strictly positive flows are stored.

It starts from UN Comtrade, where the same shipment can appear twice (exporter’s FOB report and importer’s CIF report) and the two almost never match. BACI (Gaulier and Zignago, 2010):

1. Estimates and removes CIF costs so both sides are FOB.
2. Weights each reporter by historical reliability when reconciling the two reports.

That is why BACI and raw Comtrade differ even for the same country pair. Country codes are UN Comtrade numeric codes (not always ISO numeric). Product codes must be read as text so HS leading zeros are kept.

HS02 years in this release: **2002–2024**. The most recent year is not necessarily final (BACI is built from a January Comtrade pull).

---

## 3. Headline characteristics

| Dimension | Full BACI HS02 V202601 | PIC slice (14 requested economies) |
| --------- | ---------------------- | ---------------------------------- |
| Years | **2002–2024** (23 files) | **All 23 years, all 14 PICs** |
| Records | **229,376,229** | **2,868,321** raw PIC flows → **3,030,040** PIC-as-reporter rows |
| Countries (metadata) | 238 | 14 of 14 requested |
| Products (metadata) | 5,223 HS-6 | 5,205 HS-6 and **96** HS-2 chapters in the PIC view |
| PIC–year coverage | — | **322 / 322 (100%)** |
| Focus partners AUS / CHN / USA | — | 848,904 PIC-view rows |
| Incomplete AUS/CHN/USA cells | — | **73** of 644 country–year–flow cells |

The contrast with the Comtrade Premium SITC AG3 extract is the main data-quality result: that extract had **8 of 14** reporters, **no 2000–2007 rows**, and **20%** of the requested reporter–year grid. BACI fills every PIC–year from 2002 through 2024, including Micronesia, Marshall Islands, Nauru, Niue, Tuvalu, and Vanuatu.

PIC-related flows are **1.25%** of BACI rows. Values in those rows sum to about **US$690 billion** over 2002–2024 (BACI `v` × 1,000), on the order of **0.2%** of BACI world trade value.

About **162,000** raw rows have a PIC on **both** sides; those appear twice in the reporter view (once as an export, once as an import).

---

## 4. Full-dataset year files

Each file is `BACI_HS02_Y{year}_V202601.csv` with columns `t` (year), `i` (exporter), `j` (importer), `k` (HS-6), `v` (thousand USD), `q` (metric tons).

**Table 1.** World BACI coverage by year

| Year | Records | Exporters / importers | HS-6 products | Qty missing |
| ---: | ---: | ---: | ---: | ---: |
| 2002 | 6,628,322 | 222 | 5,219 | 1.1% |
| 2003 | 7,306,482 | 222 | 5,219 | 1.1% |
| 2004 | 7,986,410 | 222 | 5,219 | 1.1% |
| 2005 | 8,504,006 | 222 | 5,219 | 1.1% |
| 2006 | 8,955,818 | 223 | 5,219 | 1.0% |
| 2007 | 9,177,831 | 223 | 5,219 | 1.6% |
| 2008 | 9,430,914 | 223 | 5,219 | 1.7% |
| 2009 | 9,327,154 | 223 | 5,218 | 1.9% |
| 2010 | 9,660,044 | 223 | 5,215 | 2.0% |
| 2011 | 9,862,639 | 225 | 5,216 | 1.9% |
| 2012 | 10,180,818 | 226 | 5,216 | 2.5% |
| 2013 | 10,357,176 | 227 | 5,212 | 1.9% |
| 2014 | 10,404,780 | 226 | 5,205 | 2.0% |
| 2015 | 10,772,335 | 226 | 5,198 | 2.7% |
| 2016 | 10,841,919 | 226 | 5,200 | 2.4% |
| 2017 | 11,126,776 | 226 | 5,146 | 2.3% |
| 2018 | 11,236,908 | 226 | 5,122 | 2.4% |
| 2019 | 11,333,137 | 226 | 5,076 | 2.4% |
| 2020 | 10,944,141 | 226 | 4,933 | 2.6% |
| 2021 | 11,467,434 | 226 | 4,936 | 2.7% |
| 2022 | 11,475,566 | 226 | 4,945 | 3.0% |
| 2023 | 11,514,720 | 226 | 4,942 | 3.5% |
| 2024 | 10,880,899 | 226 | 4,938 | 3.2% |

Row volume rises through 2023 and dips in 2024, consistent with incomplete latest-year reporting. Distinct HS-6 codes in use fall after the mid-2010s because this archive is locked to the **2002** nomenclature. Quantity is missing on **1–3.5%** of world rows (empty `q`); values are populated on recorded flows by construction.

CSV: `outputs/baci_characteristics/csv/year_stats.csv`.

---

## 5. Pacific Island coverage

Requested reporters are the same fourteen economies as the Comtrade download (UN codes 90, 184, 242, 296, 520, 548, 570, 583, 584, 585, 598, 776, 798, 882). Every one appears as both exporter and importer in **every** year 2002–2024.

**Table 2.** PIC-as-reporter view (imports where the PIC is `j`; exports where the PIC is `i`)

| Country | ISO3 | Records | Share of PIC view | HS-6 | Partners | Focus partners | Span |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Fiji | FJI | 820,318 | 27.1% | 5,095 | 223 | AUS, CHN, USA | 2002–2024 |
| Papua New Guinea | PNG | 543,209 | 17.9% | 5,087 | 225 | AUS, CHN, USA | 2002–2024 |
| Samoa | WSM | 237,696 | 7.8% | 4,711 | 203 | AUS, CHN, USA | 2002–2024 |
| Tonga | TON | 213,733 | 7.1% | 4,692 | 200 | AUS, CHN, USA | 2002–2024 |
| Vanuatu | VUT | 205,678 | 6.8% | 4,550 | 192 | AUS, CHN, USA | 2002–2024 |
| Solomon Islands | SLB | 185,573 | 6.1% | 4,477 | 197 | AUS, CHN, USA | 2002–2024 |
| Palau | PLW | 178,230 | 5.9% | 4,586 | 191 | AUS, CHN, USA | 2002–2024 |
| Kiribati | KIR | 154,095 | 5.1% | 4,275 | 179 | AUS, CHN, USA | 2002–2024 |
| Micronesia | FSM | 152,439 | 5.0% | 4,659 | 168 | AUS, CHN, USA | 2002–2024 |
| Marshall Islands | MHL | 120,073 | 4.0% | 4,141 | 173 | AUS, CHN, USA | 2002–2024 |
| Cook Islands | COK | 95,840 | 3.2% | 4,160 | 156 | AUS, CHN, USA | 2002–2024 |
| Nauru | NRU | 46,626 | 1.5% | 3,442 | 168 | AUS, CHN, USA | 2002–2024 |
| Tuvalu | TUV | 42,001 | 1.4% | 3,547 | 147 | AUS, CHN, USA | 2002–2024 |
| Niue | NIU | 34,529 | 1.1% | 3,151 | 147 | AUS, USA (**no CHN**) | 2002–2024 |

Fiji plus PNG account for **45%** of PIC-view rows. Niue has **no China HS-6 flow** in 2002–2024 (import or export).

PIC-view row counts by year run from 64,085 (2002) to a peak of 164,562 (2011) and 127,720 in 2024. All fourteen names appear in every year (CSV: `availability_by_year.csv`).

### 5.1 Imports versus exports

Imports dominate HS-6 row counts (many imported varieties; a thinner exported set):

| Flow | PIC-view rows | Value populated | Qty populated |
| --- | ---: | ---: | ---: |
| Import | 2,575,648 (85%) | 100% | 93.6% |
| Export | 454,392 (15%) | 100% | 93.5% |

Quantity completeness in the PIC slice (~93.5%) is a little weaker than the world files (mostly 97–99%). Influence indices use values only.

Fiji exports 4,502 HS-6 codes; Tuvalu exports 1,792. Import product sets are broader for every PIC (CSV: `product_coverage.csv`).

### 5.2 Australia, China, United States

HS-6 rows involving those three partners (PIC view):

| Year | AUS | CHN | USA |
| ---: | ---: | ---: | ---: |
| 2002 | 13,081 | 3,478 | 3,775 |
| 2010 | 15,604 | 11,650 | 11,924 |
| 2016 | 15,354 | **15,381** | 9,181 |
| 2024 | 14,540 | **15,846** | 6,045 |

China’s product-level row count with PICs overtakes Australia around **2016** and stays ahead. The US row count peaks near 2011 and is the lowest of the three by 2024. Row counts are not values; they show how widely each partner appears across PIC–product cells.

Of 14 × 23 × 2 = **644** country–year–flow cells, **73** miss at least one of AUS/CHN/USA. Almost all missing links are **China exports from small PICs**, especially:

| Economy | Gaps | Typical missing partner |
| --- | ---: | --- |
| Niue | 46 (every year, both flows, except a 2004 export also missing AUS) | CHN |
| Nauru | 7 | CHN (mostly early exports) |
| Palau | 7 | CHN or AUS on exports |
| Tuvalu | 5 | CHN on early exports |
| Kiribati, Micronesia | 3 each | CHN on 2002–2004 exports |
| Samoa, Tonga | 1 each | CHN on a single export year |

These are sparse-export zeros, not missing world totals. CSV: `partner_gaps.csv`.

---

## 6. Influence-index framework

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Filter BACI year files to PIC exporter or importer│
│  Layer 2: PIC-as-reporter view; HS-6 → HS-2 chapters        │
│  Layer 3: World = sum of all partners (no W00 in BACI)      │
│  Layer 4: I and E from partner / world flow totals          │
│  Layer 5: I^Y, E^Y — bilateral flows / GDP                  │
│  Layer 6: CWI and CWE — HS-2 share² × chapter/GDP × global share │
└─────────────────────────────────────────────────────────────┘
```

### 6.1 I and E

$$
I_{i,j,t}
=
\frac{\mathrm{imports}_{i,j,t}}{\mathrm{TotalImports}_{i,t}}
\qquad
E_{i,j,t}
=
\frac{\mathrm{exports}_{i,j,t}}{\mathrm{TotalExports}_{i,t}}
$$

Denominators are the PIC’s trade with **all** BACI partners, not AUS+CHN+US. Using only the three partners would overstate dependence. $I, E \in [0, 1]$ when bilateral flows are subsets of that world total.

### 6.2 GDP exposure

Let \(Y_{i,t}\) be GDP in current US dollars (World Bank WDI `NY.GDP.MKTP.CD`).

$$
I^{Y}_{i,j,t}=\frac{M_{i,j,t}}{Y_{i,t}}=I_{i,j,t}\cdot\frac{M_{i,t}}{Y_{i,t}},\qquad
E^{Y}_{i,j,t}=\frac{X_{i,j,t}}{Y_{i,t}}=E_{i,j,t}\cdot\frac{X_{i,t}}{Y_{i,t}}
$$

Cook Islands and Niue have no WDI GDP series; their I^Y, E^Y, CWI, and CWE are missing (I and E are still computed).

### 6.3 CWI and CWE

Heavy reliance on a partner that **dominates global trade** in a chapter is harder to substitute away from. Each chapter term therefore includes a global market-share factor. For partner \(j\) and HS-2 chapter \(c\):

$$
iw_{j,c,t}
=
\frac{\mathrm{TotalExports}_{j,c,t}}{\mathrm{WorldExports}_{c,t}}
\qquad
ew_{c,j,t}
=
\frac{\mathrm{TotalImports}_{j,c,t}}{\mathrm{WorldImports}_{c,t}}
$$

In BACI these are built from the full year files (not the PIC slice): \(\mathrm{TotalExports}_{j,c,t}\) sums all flows with exporter \(j\) and product in \(c\); \(\mathrm{WorldExports}_{c,t}\) sums **all** flows in chapter \(c\). \(\mathrm{TotalImports}_{j,c,t}\) uses importer \(j\). Because each BACI flow is stored once, \(\mathrm{WorldExports}_{c,t}=\mathrm{WorldImports}_{c,t}\). Partner export and import _shares_ still differ.

$$
\mathrm{CWI}_{i,j,t}
=
\sum_{c}
\left[
\left(
\frac{\mathrm{imports}_{i,j,c,t}}{\mathrm{TotalImports}_{i,c,t}}
\right)^{2}
\times
\frac{\mathrm{TotalImports}_{i,c,t}}{Y_{i,t}}
\times
iw_{j,c,t}
\right]
$$

$$
\mathrm{CWE}_{i,j,t}
=
\sum_{c}
\left[
\left(
\frac{\mathrm{exports}_{i,j,c,t}}{\mathrm{TotalExports}_{i,c,t}}
\right)^{2}
\times
\frac{\mathrm{TotalExports}_{i,c,t}}{Y_{i,t}}
\times
ew_{c,j,t}
\right]
$$

Here \(c\) is an **HS 2-digit chapter** (96 chapters). Squaring the PIC-partner share makes vulnerability rise faster as a chapter approaches exclusive reliance on \(j\). The chapter/GDP weight is how large that chapter is in the economy. Multiplying by \(iw\) (CWI) or \(ew\) (CWE) scales that up when \(j\) is a large global supplier (buyer). Unscaled HHI terms (trade weights, before GDP) are stored as `cwi_trade` / `cwe_trade`. Algebraically, \(\mathrm{CWI}=\mu\cdot\mathrm{CWI}^{\mathrm{trade}}\) with \(\mu=M/Y\).

HS-2 is not SITC-2, so CWI/CWE are not interchangeable with the Comtrade report (Comtrade CWI/CWE have no \(iw\)/\(ew\)). Values are converted from thousand USD to USD in the PIC panel; the conversion cancels in I and E and in the squared-share term.

**Panel:** 14 countries × 23 years × 3 partners = **966** I/E observations. GDP-scaled I^Y/E^Y/CWI/CWE are missing for Cook Islands and Niue (no World Bank GDP). Global shares: `outputs/baci_influence/csv/global_hs2_shares.csv`. GDP: `outputs/baci_influence/csv/gdp_current_usd.csv`.

---

## 7. Headline influence results

### 7.1 Means and medians (2002–2024)

| Partner | Obs. | Mean I | Median I | Mean E | Median E | Mean I^Y | Median I^Y | Mean E^Y | Median E^Y |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Australia | 322 | **0.137** | 0.088 | **0.091** | 0.014 | 0.083 | **0.054** | 0.034 | 0.005 |
| China | 322 | **0.112** | 0.086 | 0.067 | **0.005** | 0.866 | 0.052 | **0.038** | 0.001 |
| United States | 322 | 0.075 | 0.028 | 0.075 | 0.025 | 0.087 | 0.028 | 0.019 | 0.007 |

GDP-weighted CWI/CWE vs unscaled HHI (`cwi_trade`):

| Partner | Mean CWI | Median CWI | Mean CWE | Median CWE | Mean CWI_trade | Mean CWE_trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Australia | 0.0008 | 0.0004 | 0.0003 | 0.0000 | 0.0013 | 0.0008 |
| China | **0.039** | 0.003 | **0.003** | 0.0000 | **0.008** | 0.005 |
| United States | 0.004 | 0.001 | 0.002 | 0.0003 | 0.004 | **0.008** |

Mean \(M/Y\) ≈ 4.6 is not a typical PIC (Marshall Islands ship-registry imports). Median \(M/Y\) ≈ 0.55; median \(X/Y\) ≈ 0.31.

**Readings:**

1. Averaging across all fourteen PICs, **Australia still has the largest mean import and export shares** of the three partners. Median I^Y also ranks Australia first (0.054 vs China 0.052).
2. China’s **median E (0.005)** is far below its mean E (0.067): export exposure to China is concentrated in a few economies (above all Solomon Islands).
3. China’s **mean I^Y (0.87)** and **mean CWI (0.039)** are Marshall Islands artifacts (recorded imports often ≫ GDP). Use medians, or drop Marshall Islands, for GDP-scaled comparisons.
4. After global market shares, **CWI_trade rankings flip** toward China (world exporter) and the US (world importer). GDP scaling then re-ranks *countries*: open, import-heavy PICs (Nauru, Palau, Micronesia) rise relative to PNG.

### 7.2 Country–partner means (23 years)

| Country | Partner | Mean I | Mean E | Mean I^Y | Mean E^Y | Mean CWI | Mean CWE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nauru | Australia | **0.417** | 0.107 | **0.308** | 0.078 | 0.0034 | 0.0002 |
| Papua New Guinea | Australia | **0.376** | **0.359** | 0.107 | **0.194** | 0.0009 | 0.0023 |
| Micronesia | United States | **0.319** | 0.068 | **0.171** | 0.017 | 0.010 | 0.003 |
| Palau | United States | **0.279** | 0.076 | 0.143 | 0.008 | 0.008 | 0.002 |
| Samoa | Australia | 0.100 | **0.323** | 0.051 | 0.038 | 0.0003 | 0.0003 |
| Solomon Islands | China | 0.149 | **0.552** | 0.051 | **0.262** | 0.005 | **0.029** |
| Fiji | United States | 0.040 | **0.265** | 0.023 | 0.068 | 0.002 | 0.008 |
| Fiji | Australia | 0.194 | 0.174 | 0.109 | 0.046 | 0.0009 | 0.0004 |
| Kiribati | Australia | 0.213 | 0.037 | 0.137 | 0.006 | 0.002 | 0.0000 |
| Tuvalu | China | 0.239 | 0.005 | **0.511** | 0.002 | **0.046** | 0.0000 |
| Marshall Islands | China | 0.187 | 0.018 | 9.37 | 0.075 | 0.379 | 0.002 |
| Vanuatu | China | 0.178 | 0.023 | 0.090 | 0.006 | 0.007 | 0.0002 |
| Tonga | United States | 0.092 | 0.198 | 0.044 | 0.013 | 0.002 | 0.001 |
| Papua New Guinea | China | 0.129 | 0.142 | 0.030 | 0.073 | 0.002 | 0.005 |

Cook Islands and Niue have I/E but no I^Y/CWI (no WDI GDP). Marshall Islands I^Y/CWI should not be compared with other PICs.

**Notable patterns:**

- **Solomon Islands–China** remains the strongest *real* export case: mean E ≈ 0.55, E^Y ≈ 0.26, CWE ≈ **0.029** (2024 CWE **0.064**, `cwe_trade` 0.15). High CWE reflects concentrated chapters, China as a large global buyer, *and* exports that are a large slice of GDP.
- **PNG–Australia** still has the broadest dual **I/E** (0.38 / 0.36). I^Y (0.11) is below Nauru–Australia and Micronesia–US because PNG’s \(M/Y\) is only ~0.27, but E^Y (**0.19**) is the highest credible export exposure after Solomon–China, given \(X/Y\) ≈ 0.53. PNG–China CWE (0.005) still exceeds PNG–Australia CWE (0.002) because of China’s world import share.
- **Nauru–Australia** is the highest mean I (0.42) **and** highest credible I^Y (**0.31**): high partner share *and* imports ~84% of GDP. CWI stays small (0.003) because Australia is a small global exporter.
- **Samoa–Australia** stays export-tilted on E (0.32), but E^Y is only 0.038 because exports are ~10% of GDP.
- **North Pacific:** Micronesia–US and Palau–US remain the main US import stories on both I and I^Y (0.17 and 0.14). Marshall Islands is a China-import share story (I 0.19) whose I^Y is not economically meaningful.
- **Tuvalu–China** I^Y (0.51) is high because Tuvalu’s recorded \(M/Y\) ≈ 2.9, not because I is extreme.
- **Fiji–US** is still export-tilted (E 0.27, E^Y 0.068, CWE 0.008). Fiji–China is import-tilted.

CSV: `outputs/baci_influence/csv/summary_by_country_partner.csv`.

### 7.3 2024 snapshot

| Country | AUS I | CHN I | US I | AUS E | CHN E | US E |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cook Islands | 0.025 | 0.077 | 0.018 | 0.003 | 0.000 | 0.007 |
| Fiji | 0.138 | **0.158** | 0.057 | 0.141 | 0.041 | **0.304** |
| Kiribati | 0.114 | **0.288** | 0.015 | 0.000 | 0.000 | 0.008 |
| Marshall Islands | 0.000 | **0.416** | 0.005 | 0.000 | 0.007 | 0.020 |
| Micronesia | 0.041 | 0.186 | **0.261** | 0.001 | **0.282** | 0.006 |
| Nauru | **0.507** | 0.189 | 0.014 | 0.001 | 0.041 | 0.011 |
| Niue | 0.009 | 0.000 | 0.017 | 0.004 | 0.000 | **0.504** |
| Palau | 0.016 | **0.244** | 0.104 | 0.000 | 0.000 | 0.076 |
| Papua New Guinea | **0.291** | 0.243 | 0.009 | 0.194 | **0.235** | 0.006 |
| Samoa | 0.089 | **0.144** | 0.078 | 0.106 | 0.021 | 0.084 |
| Solomon Islands | 0.125 | **0.374** | 0.012 | 0.136 | **0.585** | 0.002 |
| Tonga | 0.087 | **0.235** | 0.054 | 0.098 | 0.003 | 0.122 |
| Tuvalu | 0.113 | **0.260** | 0.007 | 0.000 | 0.000 | 0.002 |
| Vanuatu | 0.136 | **0.344** | 0.009 | 0.009 | 0.060 | 0.044 |

By 2024, **China is the largest of the three import partners** for Fiji, Kiribati, Marshall Islands, Palau, Samoa, Solomon Islands, Tonga, Tuvalu, and Vanuatu. Australia remains first for **Nauru** and **PNG** (with China close on PNG imports and ahead on PNG exports). The US remains first for **Micronesia** imports. Treat 2024 as provisional.

### 7.4 Early versus late window (mean I, 2002–2008 vs 2018–2024)

Largest **increases** in mean I are all China: Solomon Islands +0.28, Palau +0.22, Marshall Islands +0.21, Vanuatu +0.19, PNG +0.14, Kiribati +0.13, Micronesia +0.12, Samoa +0.11, Fiji +0.11.

Largest **declines** in mean I: Kiribati–Australia −0.22, PNG–Australia −0.22, Palau–US −0.18, Fiji–Australia −0.12, Solomon Islands–Australia −0.12.

The same windows show Solomon Islands–China **E** up +0.17 and PNG–China **E** up +0.11, while PNG–Australia E falls −0.18 and Micronesia–US E falls −0.16.

---

## 8. Time-series figures

Each panel is one PIC. Blue = Australia, red = China, green = United States. Partner-specific figures (all PICs on one chart) are in the same folder.

### 8.1 Import index (I)

![BACI import index by country](../outputs/baci_influence/plots/timeseries_import_index_baci.png)

![BACI I — Australia](../outputs/baci_influence/plots/timeseries_import_index_baci_by_partner_aus.png)

![BACI I — China](../outputs/baci_influence/plots/timeseries_import_index_baci_by_partner_china.png)

![BACI I — United States](../outputs/baci_influence/plots/timeseries_import_index_baci_by_partner_us.png)

**Observations:**

- China’s import share rises in almost every PIC after about 2010. By the 2020s it is the top of the three in several Melanesian and Micronesian series (Solomon Islands, Vanuatu, Marshall Islands, Tuvalu, Tonga).
- Australia starts high in Fiji, Kiribati, Nauru, PNG, and Solomon Islands, then declines or flattens as China’s I rises. **Nauru–Australia** stays the highest I series (often 0.4–0.8) but is noisy.
- The US is the main import partner for **Micronesia** and, in the early sample, **Palau**. Palau’s US I falls while Palau’s China I rises; by 2024 China leads Palau imports among the three.
- **Cook Islands** China I is volatile (including a spike around 2019). **Niue** I for all three partners stays very low.

### 8.2 Export index (E)

![BACI export index by country](../outputs/baci_influence/plots/timeseries_export_index_baci.png)

![BACI E — Australia](../outputs/baci_influence/plots/timeseries_export_index_baci_by_partner_aus.png)

![BACI E — China](../outputs/baci_influence/plots/timeseries_export_index_baci_by_partner_china.png)

![BACI E — United States](../outputs/baci_influence/plots/timeseries_export_index_baci_by_partner_us.png)

**Observations:**

- **Solomon Islands–China** is the standout: E rises through the 2000s and stays near 0.5–0.7.
- **Samoa–Australia** is very high in the 2000s (E often above 0.5) and then declines.
- **PNG:** Australia’s export share is high early and eases; China’s export share trends up and in 2024 exceeds Australia.
- **Fiji–US** exports sit well above Fiji–US imports for most of the sample.
- Small-export PICs (Niue, Tuvalu, Kiribati, Palau, Cook Islands) produce **spiky** E series: thin denominators, not stable long-run dependence. Niue–US E in 2024 (0.50) should be read that way.

### 8.3 GDP exposure (I^Y and E^Y)

![BACI I^Y by country](../outputs/baci_influence/plots/timeseries_import_index_gdp_baci.png)

![BACI I^Y — Australia](../outputs/baci_influence/plots/timeseries_import_index_gdp_baci_by_partner_aus.png)

![BACI I^Y — China](../outputs/baci_influence/plots/timeseries_import_index_gdp_baci_by_partner_china.png)

![BACI I^Y — United States](../outputs/baci_influence/plots/timeseries_import_index_gdp_baci_by_partner_us.png)

![BACI E^Y by country](../outputs/baci_influence/plots/timeseries_export_index_gdp_baci.png)

![BACI E^Y — Australia](../outputs/baci_influence/plots/timeseries_export_index_gdp_baci_by_partner_aus.png)

![BACI E^Y — China](../outputs/baci_influence/plots/timeseries_export_index_gdp_baci_by_partner_china.png)

![BACI E^Y — United States](../outputs/baci_influence/plots/timeseries_export_index_gdp_baci_by_partner_us.png)

Marshall Islands (and, to a lesser extent, Tuvalu) dominate the China I^Y panel because recorded imports exceed GDP. Cook Islands and Niue are blank (no WDI GDP).

### 8.4 CWI and CWE

CWI/CWE rise when a partner dominates **important** HS-2 chapters, that partner is a large global supplier (CWI) or buyer (CWE), *and* the flow is large relative to GDP. Because \(iw\) and \(ew\) are typically 0.01–0.16, CWI/CWE levels are much smaller than I/E.

| Pattern | Meaning |
| ------- | ------- |
| High I, low I^Y / CWI | Concentrated partner, but imports are a small slice of GDP (or the partner is a small world exporter) |
| High E, low E^Y / CWE | Concentrated export partner, but exports are a small slice of GDP |
| High E^Y and CWE | Large export share of GDP, concentrated chapters, and a large global buyer |

![BACI CWI by country](../outputs/baci_influence/plots/timeseries_cwi_baci.png)

![BACI CWI — Australia](../outputs/baci_influence/plots/timeseries_cwi_baci_by_partner_aus.png)

![BACI CWI — China](../outputs/baci_influence/plots/timeseries_cwi_baci_by_partner_china.png)

![BACI CWI — United States](../outputs/baci_influence/plots/timeseries_cwi_baci_by_partner_us.png)

![BACI CWE by country](../outputs/baci_influence/plots/timeseries_cwe_baci.png)

![BACI CWE — Australia](../outputs/baci_influence/plots/timeseries_cwe_baci_by_partner_aus.png)

![BACI CWE — China](../outputs/baci_influence/plots/timeseries_cwe_baci_by_partner_china.png)

![BACI CWE — United States](../outputs/baci_influence/plots/timeseries_cwe_baci_by_partner_us.png)

**Observations:**

- **Solomon Islands–China CWE** is still the standout among credible series (mean 0.029; **0.064 in 2024**).
- **PNG–Australia CWE** stays low (0.002) despite high E, because Australia’s world import share is small. PNG–China CWE (0.005) is larger.
- **Nauru–Australia** is a high I^Y case (0.31), not a high CWI case (0.003) — Australia is a small global exporter.
- **Samoa–Australia CWE** is tiny (~0.0003) after both global-share and \(X/Y\) scaling.
- **Micronesia / Palau CWI** with the US remain the main North Pacific import-concentration stories among series with plausible \(M/Y\).
- **Marshall Islands–China CWI** (mean 0.38) tracks the ship-registry import/GDP ratio, not household dependence.

---

## 9. Synthesis

### 9.1 Partner “spheres” on the complete BACI panel

| Sphere | Typical PICs | Dominant flow / partner |
| ------ | ------------ | ----------------------- |
| Australian | Nauru, PNG, (historically) Fiji, Kiribati, Samoa | Australia on imports; Samoa and PNG also on exports |
| Chinese | Solomon Islands; increasingly Marshall Islands, Vanuatu, Tuvalu, Tonga on **imports** | China on Solomon **exports**; China import shares rising almost everywhere |
| American | Micronesia, Palau (imports); Fiji (exports) | United States on Compact-state imports; Fiji–US exports |

Splitting I from E still matters. Solomon Islands remains a **China-export** story with Australian imports still material. Samoa remains an **Australia-export** story with more mixed imports. Fiji’s US link is stronger on exports than imports.

The global-share term **re-ranks partners** on CWI/CWE. GDP scaling then **re-ranks countries**: Nauru–Australia and Micronesia–US look more exposed than PNG–Australia on I^Y, even though PNG’s I is higher. PNG remains the dual-exposure case on E^Y because its export/GDP ratio is large.

### 9.2 What BACI adds relative to Comtrade

| Dimension | Comtrade SITC AG3 extract | BACI HS02 V202601 |
| --------- | ------------------------- | ----------------- |
| PICs with indices | 8 | **14** |
| Years | 2008–2024, gappy | **2002–2024, complete** |
| Country–year–partner obs. | 210 | **966** |
| World denominator | Reporter `W00` | Sum of all partners |
| Commodity for CWI/CWE | SITC-2 | HS-2 |
| Global market share in CWI/CWE | Not applied | Partner world export share (CWI) / world import share (CWE) |
| GDP weight in CWI/CWE and I^Y/E^Y | \(M/Y\), \(X/Y\) (WDI) | \(M/Y\), \(X/Y\) (WDI) |
| Valuation | CIF imports / FOB exports (+ primary fallback) | Reconciled FOB |

The qualitative map is consistent where both sources overlap (Solomon Islands–China exports; PNG–Australia; Samoa–Australia exports; Palau/Micronesia–US imports). BACI’s extra six economies and pre-2008 years show that **China’s import-share rise is Pacific-wide**, including Marshall Islands, Tuvalu, Vanuatu, and Tonga, which the Comtrade AG3 extract largely missed.
