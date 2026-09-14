# Trade Influence Indices: I, E, CWI, and CWE

## 1. Objectives and research question

### 1.1 Research question

> Evaluate Pacific Island Countries’ (PICs) **vulnerability to foreign influence through trade** with Australia, China, and the United States, using partner shares of total imports and exports rather than raw bilateral values.

This analysis uses:

| Index | Full name | Role |
| ----- | --------- | ---- |
| **I** | Import index | Partner share of total imports |
| **E** | Export index | Partner share of total exports |
| **CWI** | Commodity Weighted Import index | Partner concentration in important import commodities (HHI-style) |
| **CWE** | Commodity Weighted Export index | Partner concentration in important export commodities (HHI-style) |

Import and export are **not** combined into a single trade-share index. CWI and CWE likewise remain flow-specific.

### 1.2 Scope

| Source | Index | Partners | Countries | Years |
| ------ | ----- | -------- | --------- | ----- |
| **UN Comtrade** | I, E, CWI, CWE | Australia, China, United States | 8 PICs (incl. Cook Islands) | 2008–2024 (varies) |
| **IMF Pacific DOTS** | I, E only | Australia, China, United States | 12 PICs | 2000–2024 |

CWI and CWE require commodity-level detail. IMF DOTS is aggregate only, so **CWI/CWE are Comtrade-only**. Denominators are **world totals** (`W00` / IMF `*_world`), not the sum of the three partners.

---

## 2. Analytical framework

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Data preparation                                  │
│  Comtrade SITC AG3 → SITC-2 panel; IMF wide → long totals   │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Import / export indices (I, E)                    │
│  Comtrade + IMF (AUS, CHN, US); world denominators          │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Commodity-weighted indices (CWI, CWE)             │
│  Comtrade only — SITC-2 partner share² × commodity weight   │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Cross-source comparison                           │
│  Overlay Comtrade vs IMF I and E where they overlap         │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Time-series visualization                         │
│  By country and by partner                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Index definitions

### 3.1 Import and export indices

For PIC $i$, partner $j$, year $t$:

$$
I_{i,j,t}
=
\frac{\mathrm{imports}_{i,j,t}}{\mathrm{TotalImports}_{i,t}}
\qquad
E_{i,j,t}
=
\frac{\mathrm{exports}_{i,j,t}}{\mathrm{TotalExports}_{i,t}}
$$

Where:

- $i$ = PIC (reporter)
- $j$ = partner (Australia, China, or the United States)
- $t$ = year

Notes:

- Numerators are bilateral flows with $j$.
- Denominators are **world totals** (Comtrade `W00` / IMF `*_world`). Using only AUS+CHN+US as “total” would overstate dependence.
- $I_{i,j,t}, E_{i,j,t} \in [0, 1]$ when bilateral flows are subsets of world totals. Higher values mean a larger share of the PIC’s imports (exports) is with that partner.

### 3.2 Commodity Weighted Import / Export indices

HHI-style (squared partner dependence × commodity importance):

$$
\mathrm{CWI}_{i,j,t}
=
\sum_{c}
\left[
\left(
\frac{\mathrm{imports}_{i,j,c,t}}{\mathrm{TotalImports}_{i,c,t}}
\right)^{2}
\times
\left(
\frac{\mathrm{TotalImports}_{i,c,t}}{\mathrm{TotalImports}_{i,t}}
\right)
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
\left(
\frac{\mathrm{TotalExports}_{i,c,t}}{\mathrm{TotalExports}_{i,t}}
\right)
\right]
$$

Where $c$ is a **SITC Rev.4 2-digit** division, rolled up from AG3 group codes.

The first term is partner dependence on $j$ for commodity $c$; it is **squared** so that vulnerability rises non-linearly as the PIC approaches complete reliance on a single partner. The second term is commodity importance in total imports (exports).

Interpretation:

- Squared partner share is high when a partner dominates a given commodity.
- Commodity weight is high when that commodity is important in total trade.
- CWI/CWE are therefore high when a partner is concentrated in **large** import/export divisions — not merely when overall bilateral volume is large.

I/E and CWI/CWE are related but not interchangeable: I or E can be high with diversified commodity links; CWI/CWE rise further when links are concentrated in key divisions.

---

## 4. Input data and preparation

### 4.1 UN Comtrade

| Item | Detail |
| ---- | ------ |
| Classification | SITC Rev.4, AG3 (3-digit groups) |
| Countries | Cook Islands, Fiji, Kiribati, Palau, Papua New Guinea, Samoa, Solomon Islands, Tonga |
| Partners | `AUS`, `CHN`, `USA`, `W00` (world) |
| Commodity | AG3 codes padded to 3 digits (so `11` → `011`) then rolled to SITC-2 |
| Valuation | Imports CIF; exports FOB; `primaryValue` fallback |

SITC-2 panel construction (`trade_influence.prepare.build_sitc2_panel`):

```
country × year × flow × partner × sitc2 → value_usd
```

World totals always use `partner = world` (`W00`).

### 4.2 IMF Pacific DOTS

| Item | Detail |
| ---- | ------ |
| Countries | 12 Pacific economies (includes Vanuatu, Tuvalu, Marshall Islands, Micronesia, Nauru) |
| Partners | Australia, China, US, World |
| Units | Millions USD (scale cancels in I and E) |
| Commodity | None → I and E only |

IMF country labels are mapped to short Comtrade-style names where a match exists (e.g. `Fiji, Republic of` → `Fiji`) for overlay plots.

### 4.3 Coverage contrast

| Dimension | Comtrade | IMF |
| --------- | -------- | --- |
| Countries with I/E | 8 | 12 |
| Partners | AUS, CHN, US | AUS, CHN, US |
| Country–year–partner observations | 210 | 900 |
| Year span | 2008–2024 (uneven) | 2000–2024 |
| CWI / CWE | Yes | No |

Comtrade coverage by country (years with indices):

| Country | Years | Window |
| ------- | ----- | ------ |
| Fiji | 17 | 2008–2024 |
| Samoa | 15 | 2009–2024 (gap 2020) |
| Tonga | 14 | 2008–2023 (gaps 2015–2016) |
| Papua New Guinea | 7 | 2011–2012, 2019–2023 |
| Kiribati | 7 | 2014–2021 (gap 2019) |
| Palau | 5 | 2014–2018 |
| Solomon Islands | 4 | 2015–2018 |
| Cook Islands | 1 | 2008 |

Cook Islands, Solomon Islands, Palau, and PNG have short Comtrade panels; treat their Comtrade indices as illustrative, not long-run trends.

---

## 5. Headline results

### 5.1 I and E by source and partner

| Source | Partner | Obs. | Countries | Years | Mean I | Median I | Mean E | Median E |
| ------ | ------- | ---- | --------- | ----- | ------ | -------- | ------ | -------- |
| Comtrade | Australia | 70 | 8 | 2008–2024 | **0.148** | 0.141 | **0.183** | 0.122 |
| Comtrade | China | 70 | 8 | 2008–2024 | **0.106** | 0.103 | **0.067** | 0.011 |
| Comtrade | United States | 70 | 8 | 2008–2024 | **0.082** | 0.061 | **0.103** | 0.105 |
| IMF | Australia | 300 | 12 | 2000–2024 | **0.204** | 0.179 | **0.125** | 0.055 |
| IMF | China | 300 | 12 | 2000–2024 | **0.071** | 0.047 | **0.061** | 0.001 |
| IMF | United States | 300 | 12 | 2000–2024 | **0.077** | 0.035 | **0.068** | 0.030 |

Comtrade CWI / CWE means (same 70 observations per partner):

| Partner | Mean CWI | Median CWI | Mean CWE | Median CWE |
| ------- | -------- | ---------- | -------- | ---------- |
| Australia | 0.055 | 0.045 | **0.137** | 0.075 |
| China | 0.029 | 0.027 | 0.040 | 0.001 |
| United States | 0.033 | 0.018 | 0.053 | 0.031 |

**Findings:**

1. On the **8-country Comtrade sample**, Australia is the largest of the three partners for both mean I and mean E. China’s mean I (0.11) exceeds its mean E (0.07); the US is the reverse (mean E 0.10 > mean I 0.08).
2. On the **full 12-country IMF panel**, Australia’s mean I (~0.20) clearly exceeds China (~0.07) and the US (~0.08). Export medians for China are near zero, so a few high-export-exposure economies pull the China E mean up.
3. Mean CWE for Australia (0.14) is well above mean CWI (0.05): Australian **export** concentration in key SITC-2 divisions is stronger than import concentration on average.

### 5.2 Comtrade country averages

Selected country–partner means (years as in the coverage table):

| Country | Partner | Years | Mean I | Mean E | Mean CWI | Mean CWE |
| ------- | ------- | ----- | ------ | ------ | -------- | -------- |
| Fiji | Australia | 17 | 0.169 | 0.142 | 0.060 | 0.093 |
| Fiji | China | 17 | 0.123 | 0.033 | 0.036 | 0.008 |
| Fiji | United States | 17 | 0.043 | 0.163 | 0.013 | 0.096 |
| Kiribati | Australia | 7 | 0.190 | 0.048 | 0.079 | 0.028 |
| Palau | United States | 5 | **0.295** | 0.184 | **0.173** | 0.141 |
| Papua New Guinea | Australia | 7 | **0.347** | 0.265 | 0.154 | 0.235 |
| Papua New Guinea | China | 7 | 0.145 | 0.153 | 0.039 | 0.062 |
| Samoa | Australia | 15 | 0.112 | **0.330** | 0.033 | **0.274** |
| Solomon Islands | China | 4 | 0.132 | **0.631** | 0.034 | **0.517** |
| Tonga | Australia | 14 | 0.078 | 0.221 | 0.021 | 0.144 |
| Tonga | United States | 14 | 0.107 | 0.119 | 0.035 | 0.036 |

**Notable patterns:**

- **Solomon Islands–China exports** are the strongest Comtrade exposure: mean E ≈ 0.63 and mean CWE ≈ 0.52 (short 2015–2018 window). High CWE relative to E is limited here; both are high, so the link is large **and** concentrated in important export divisions.
- **PNG–Australia**: highest mean I (0.35) and high CWE (0.24) — import share and export commodity concentration with Australia are both marked (short sample).
- **Samoa–Australia**: moderate I (~0.11) but high E (~0.33) and CWE (~0.27) — export dependence and concentration, not import share.
- **Palau–US**: highest US import exposure (mean I ≈ 0.30, CWI ≈ 0.17). Australia and China are small.
- **Fiji–US**: low I (~0.04) but higher E (~0.16) and CWE (~0.10) — the US matters more on the export side.
- **Tonga / Kiribati**: Australia leads imports; Tonga’s E with Australia is also elevated (~0.22).

### 5.3 IMF country averages (I and E; 25 years)

Selected contrasts (mean I / mean E):

| Country | AUS I | AUS E | CHN I | CHN E | US I | US E |
| ------- | ----- | ----- | ----- | ----- | ---- | ---- |
| Papua New Guinea | **0.399** | **0.288** | 0.122 | 0.114 | 0.027 | 0.018 |
| Nauru | **0.476** | 0.111 | 0.031 | 0.002 | 0.048 | 0.028 |
| Vanuatu | **0.280** | 0.148 | 0.091 | 0.055 | 0.019 | 0.051 |
| Kiribati | **0.269** | 0.172 | 0.068 | 0.007 | 0.031 | 0.055 |
| Solomon Islands | 0.251 | 0.065 | 0.147 | **0.468** | 0.025 | 0.005 |
| Samoa | 0.141 | **0.468** | 0.070 | ≈0 | 0.108 | 0.082 |
| Fiji | 0.213 | 0.145 | 0.092 | 0.021 | 0.043 | 0.149 |
| Palau | 0.009 | 0.006 | 0.039 | 0.001 | **0.290** | 0.093 |
| Micronesia | 0.113 | ≈0 | 0.023 | 0.027 | **0.202** | 0.112 |

**Findings:**

- **Melanesia / South Pacific** (PNG, Vanuatu, Fiji, Kiribati, Nauru, Tuvalu): Australia typically the largest import partner of the three.
- **Solomon Islands**: China dominates **exports** (mean E ≈ 0.47); Australia still leads imports.
- **Samoa**: Australia dominates **exports** (mean E ≈ 0.47), consistent with Comtrade CWE.
- **North Pacific** (Palau, Micronesia): **US** dominates imports; Australia is small for Palau.

---

## 6. Time-series results

### 6.1 Comtrade import index (I)

Each panel is one PIC.

![Comtrade import index by country](../outputs/trade_influence/plots/timeseries_import_index_comtrade.png)

![Comtrade I — Australia](../outputs/trade_influence/plots/timeseries_import_index_comtrade_by_partner_aus.png)

![Comtrade I — China](../outputs/trade_influence/plots/timeseries_import_index_comtrade_by_partner_china.png)

![Comtrade I — United States](../outputs/trade_influence/plots/timeseries_import_index_comtrade_by_partner_us.png)

**Observations:**

- **PNG** has the highest Australian import share (~0.30–0.40) in every Comtrade year it reports.
- **Fiji** has stable dual import exposure: Australia and China both sit in a 0.13–0.22 band after 2014; the US stays lower except for a 2021 spike.
- **Palau** is a US-import story (I often above 0.30); Australia and China are near zero. Cook Islands has no Comtrade imports in 2008.
- **Tonga** is the one series where China overtakes Australia on imports by the early 2020s.
- **Kiribati** and **Solomon Islands** still show Australia leading imports in their short windows, with China rising.

### 6.2 Comtrade export index (E)

![Comtrade export index by country](../outputs/trade_influence/plots/timeseries_export_index_comtrade.png)

![Comtrade E — Australia](../outputs/trade_influence/plots/timeseries_export_index_comtrade_by_partner_aus.png)

![Comtrade E — China](../outputs/trade_influence/plots/timeseries_export_index_comtrade_by_partner_china.png)

![Comtrade E — United States](../outputs/trade_influence/plots/timeseries_export_index_comtrade_by_partner_us.png)

**Observations:**

- **Solomon Islands–China** is the strongest export exposure (E ≈ 0.55–0.67 in 2015–2018).
- **Samoa–Australia** starts very high (E > 0.5 around 2009) and declines toward the 2010s, remaining the main Australian export story.
- **Fiji–US** exports often exceed Fiji–US imports; China is a small Fiji export partner.
- **PNG** exports more to Australia than to China or the US in the available years.
- **Tonga** export shares are noisy (thin denominators); treat spikes as coverage-sensitive.

### 6.3 Comtrade CWI and CWE

CWI/CWE rise when a partner dominates **important** SITC-2 divisions, not only when overall I or E is large.

| Pattern | Meaning |
| ------- | ------- |
| CWI ≈ I (or CWE ≈ E) | Partner share is spread across commodities roughly in line with overall volume |
| CWI ≫ I (or CWE ≫ E) | Partner dominates key divisions (higher influence intensity) |
| CWI ≪ I (or CWE ≪ E) | Partner trade is large but more diversified across divisions |

![Comtrade CWI by country](../outputs/trade_influence/plots/timeseries_cwi_comtrade.png)

![Comtrade CWI — Australia](../outputs/trade_influence/plots/timeseries_cwi_comtrade_by_partner_aus.png)

![Comtrade CWI — China](../outputs/trade_influence/plots/timeseries_cwi_comtrade_by_partner_china.png)

![Comtrade CWI — United States](../outputs/trade_influence/plots/timeseries_cwi_comtrade_by_partner_us.png)

![Comtrade CWE by country](../outputs/trade_influence/plots/timeseries_cwe_comtrade.png)

![Comtrade CWE — Australia](../outputs/trade_influence/plots/timeseries_cwe_comtrade_by_partner_aus.png)

![Comtrade CWE — China](../outputs/trade_influence/plots/timeseries_cwe_comtrade_by_partner_china.png)

![Comtrade CWE — United States](../outputs/trade_influence/plots/timeseries_cwe_comtrade_by_partner_us.png)

**Observations:**

- **Solomon Islands–China CWE** (~0.40–0.55) matches the high export share: concentration in key export divisions, not a diversified China export mix.
- **Samoa–Australia CWE** is elevated early in the sample (above 0.4) and then falls — the same decline seen in E.
- **PNG–Australia** shows high CWE as well as high I: import share and export commodity concentration both point to Australia.
- **Palau–US CWI** is the main high-intensity **import** case; AUS/CHN CWI stay negligible.
- **Fiji–China CWE** stays near zero while Fiji–China I is moderate → China matters more as an import supplier than as a concentrated export destination.

### 6.4 IMF import and export indices

Twelve PICs, 2000–2024. Short names: Marshall Islands, Micronesia, Nauru.

![IMF import index by country](../outputs/trade_influence/plots/timeseries_import_index_imf.png)

![IMF I — Australia](../outputs/trade_influence/plots/timeseries_import_index_imf_by_partner_aus.png)

![IMF I — China](../outputs/trade_influence/plots/timeseries_import_index_imf_by_partner_china.png)

![IMF I — United States](../outputs/trade_influence/plots/timeseries_import_index_imf_by_partner_us.png)

![IMF export index by country](../outputs/trade_influence/plots/timeseries_export_index_imf.png)

![IMF E — Australia](../outputs/trade_influence/plots/timeseries_export_index_imf_by_partner_aus.png)

![IMF E — China](../outputs/trade_influence/plots/timeseries_export_index_imf_by_partner_china.png)

![IMF E — United States](../outputs/trade_influence/plots/timeseries_export_index_imf_by_partner_us.png)

**Observations:**

- **Australia** leads imports for PNG, Nauru, Vanuatu, Kiribati, Solomon Islands, Tuvalu, and (most years) Fiji.
- **Solomon Islands** China **exports** rise through the 2010s and overtake Australia; China imports also rise but from a lower base.
- **Samoa** Australia **exports** remain the standout IMF export series (mean E ≈ 0.47).
- **Palau** and **Micronesia**: US dominates imports. Palau’s Australian import share is essentially zero.
- **Marshall Islands** China imports jump after the mid-2010s (short, volatile series).
- **Nauru** Australian imports are the highest IMF I series (often 0.4–0.8) but are noisy.

### 6.5 Overlay: Comtrade vs IMF

Solid = Comtrade; dashed = IMF. Country grids show all three partners; partner charts isolate one partner so source agreement is easier to read.

![Import index Comtrade vs IMF, by country](../outputs/trade_influence/plots/timeseries_import_index_comtrade_vs_imf.png)

![Import index I — Australia overlay](../outputs/trade_influence/plots/timeseries_import_index_comtrade_vs_imf_by_partner_aus.png)

![Import index I — China overlay](../outputs/trade_influence/plots/timeseries_import_index_comtrade_vs_imf_by_partner_china.png)

![Import index I — United States overlay](../outputs/trade_influence/plots/timeseries_import_index_comtrade_vs_imf_by_partner_us.png)

![Export index Comtrade vs IMF, by country](../outputs/trade_influence/plots/timeseries_export_index_comtrade_vs_imf.png)

![Export index E — Australia overlay](../outputs/trade_influence/plots/timeseries_export_index_comtrade_vs_imf_by_partner_aus.png)

![Export index E — China overlay](../outputs/trade_influence/plots/timeseries_export_index_comtrade_vs_imf_by_partner_china.png)

![Export index E — United States overlay](../outputs/trade_influence/plots/timeseries_export_index_comtrade_vs_imf_by_partner_us.png)

**Selected same-year comparisons**

| Country | Year | Partner | Comtrade I | IMF I | Comtrade E | IMF E |
| ------- | ---- | ------- | ---------- | ----- | ---------- | ----- |
| Fiji | 2024 | Australia | 0.146 | 0.137 | 0.120 | 0.094 |
| Fiji | 2024 | China | 0.162 | 0.151 | 0.029 | 0.022 |
| Papua New Guinea | 2021 | Australia | 0.356 | 0.327 | 0.174 | 0.172 |
| Solomon Islands | 2018 | China | 0.149 | 0.244 | 0.668 | 0.663 |
| Palau | 2018 | United States | 0.348 | 0.258 | 0.026 | 0.025 |

Export levels are often close in overlapping years (Solomon Islands–China E; PNG–Australia E). Import levels can diverge more (Solomon Islands–China I; Palau–US I) — consistent with the separate Comtrade–IMF discrepancy analysis. Where they diverge, treat absolute I levels with caution and emphasise **rankings and trends**.

---

## 7. Synthesis: influence patterns

### 7.1 Three partner “spheres”

| Sphere | Typical PICs | Dominant flow / partner |
| ------ | ------------ | ----------------------- |
| Australian | PNG, Vanuatu, Nauru, Kiribati, Fiji, Samoa | Australia on imports; Samoa also on exports |
| Chinese | Solomon Islands | China on **exports** |
| American | Palau, Micronesia | United States on **imports** |

Splitting I from E matters: Solomon Islands is a China-export story with Australian imports still large; Samoa is an Australia-export story with more mixed imports.

### 7.2 Where commodity concentration amplifies vulnerability (Comtrade)

| Link | Signal |
| ---- | ------ |
| Solomon Islands–China | Highest E **and** CWE → large export share + concentrated divisions |
| Samoa–Australia | High E and CWE with only moderate I |
| PNG–Australia | High I and high CWE |
| Palau–US | High I and CWI; AUS/CHN negligible |
| Fiji–China | Moderate I, much lower E and CWE → more diversified / import-tilted China trade |
