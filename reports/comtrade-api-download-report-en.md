# Retrieval of Pacific Island Merchandise Trade Statistics from UN Comtrade: Technical Report

**Classification and extract:** Standard International Trade Classification, Revision 4 (SITC Rev. 4), three-digit aggregates (`AG3`)  
**Period:** 2000–2024 (annual)  
**Subscription:** UN Comtrade Premium Institutional Pro  
**Software:** `comtradeapicall` (≥ 1.3.2); implementation package `comtrade_download/`

---

## 1. Purpose and scope

### 1.1 Purpose

This report documents the specification, authentication, retrieval strategy, and post-processing of an official UN Comtrade extract used as an input to subsequent Pacific Island trade analyses (discrepancy measurement, influence indices, and anomaly detection). The extract is obtained through the Comtrade Premium Institutional Pro application programming interfaces (APIs), via the official Python client `comtradeapicall`.

The report is intended to make the download reproducible and to record design choices that are not self-evident from the portal interface alone, in particular: (i) the mapping from Comtrade Plus query fields to API parameters; (ii) the use of UN M49 area codes rather than ISO 3166-1 alpha-3 codes; and (iii) the preference for asynchronous final-data jobs over synchronous `getFinalData` calls for SITC three-digit extracts.

### 1.2 Scope

The request is confined to:

- merchandise trade (goods);
- annual frequency;
- SITC Rev. 4, all three-digit commodity groups (`AG3`);
- imports and exports (excluding re-exports and re-imports);
- fourteen Pacific Island reporters and four partners (Australia, China, the United States grouping, and World);
- calendar years 2000–2024.

A characterization of the published extract (years, reporters, and reporter–year coverage) is in [`comtrade-api-data-characteristics-report-en.md`](comtrade-api-data-characteristics-report-en.md). Analysis of trade values, discrepancies, and anomalies remains outside the scope of this document.

### 1.3 Sources of specification

The query was specified against the Comtrade Plus interactive interface and translated into API arguments. Authoritative references are the [UN Comtrade Help Center](https://uncomtrade.org/docs), the [Comtrade Plus](https://comtradeplus.un.org) portal, and the [`comtradeapicall`](https://github.com/uncomtrade/comtradeapicall) library.

---

## 2. Data request specification

### 2.1 Selection criteria

Table 1 records the correspondence between portal fields, API arguments, and project constants (`comtrade_download/constants.py`).

**Table 1.** Selection criteria for the Pacific SITC Rev. 4 AG3 extract

| Portal field | Specified value | API argument | Constant |
| --- | --- | --- | --- |
| Type of product | Goods | `typeCode='C'` | `TYPE_CODE` |
| Frequency | Annual | `freqCode='A'` | `FREQ_CODE` |
| Classification | SITC Rev. 4 | `clCode='S4'` | `CLASSIFICATION_CODE` |
| Commodity codes | AG3 | `cmdCode='AG3'` | `CMD_CODE` |
| Periods | 2000–2024 | `period='2000,2001,…,2024'` | `PERIODS` |
| Reporters | 14 Pacific Island economies | `reporterCode` (M49 list) | `REPORTER_CODES` |
| Partners | Australia; China; USA, Puerto Rico and US Virgin Islands; World | `partnerCode='36,156,842,0'` | `PARTNER_CODES` |
| Second partner | World | `partner2Code='0'` | `PARTNER2_CODE` |
| Trade flows | Imports and exports | `flowCode='M,X'` | `FLOW_CODE` |
| Mode of transport | TOTAL | `motCode='0'` | `MOT_CODE` |
| Customs procedure | TOTAL | `customsCode='C00'` | `CUSTOMS_CODE` |

`AG3` requests all three-digit SITC groups rather than a single `TOTAL` aggregate. Mode of transport `0` and customs code `C00` retain the published totals in plus breakdown, without expanding the extract across transport or customs procedures.

### 2.2 Query options

**Table 2.** Query options

| Portal field | Specified value | API argument | Role |
| --- | --- | --- | --- |
| Breakdown mode | Plus | `breakdownMode='plus'` | Returns partner, product, mode of transport, customs procedure, and second partner |
| Aggregate by | None | `aggregateBy=None` | No further collapsing of dimensions |
| Maximum records (synchronous only) | 250,000 | `maxRecords=250000` | Premium per-call ceiling; omitted on asynchronous jobs |
| Output format (synchronous only) | JSON | `format_output='JSON'` | Sole format parsed by `comtradeapicall` |
| Include descriptions (synchronous only) | Yes | `includeDesc=True` | Populates reporter and partner labels and ISO codes |

Plus mode is required to match the portal query. With transport and customs held at their TOTAL codes, the additional dimensions do not multiply the row count relative to a classic partner-by-product extract.

A preliminary count request (`getCountFinalData`) for all fourteen reporters in 2022 returned 5,005 records, well below the 250,000-record synchronous limit. Retrieval cost is therefore dominated by server-side expansion of `AG3`, not by output volume.

---

## 3. Geographic coverage

### 3.1 Coding system

Comtrade identifies reporters and partners by **UN M49 numeric area codes** in `reporterCode` and `partnerCode`. ISO 3166-1 alpha-3 codes appear only in description fields (`reporterISO`, `partnerISO`) when those fields are populated.

The helper `comtradeapicall.convertCountryIso3ToCode` maps ISO3 strings to M49 codes and is suitable for unambiguous economies. It is **not** used for the United States partner in this extract. Conversion of `USA` returns three codes (`840`, `841`, and `842`). The portal label “USA, Puerto Rico and US Virgin Islands” corresponds to **842** only, as confirmed by the Comtrade Plus query string (`Partners=842`). World is coded `0` in the API and stored as `W00` in ISO fields, consistent with downstream analysis constants (`COMTRADE_PARTNER_ISO`).

### 3.2 Reporters

**Table 3.** Requested reporters

| Comtrade label | M49 | ISO3 |
| --- | --- | --- |
| Cook Isds | 184 | COK |
| Fiji | 242 | FJI |
| FS Micronesia | 583 | FSM |
| Kiribati | 296 | KIR |
| Marshall Isds | 584 | MHL |
| Nauru | 520 | NRU |
| Niue | 570 | NIU |
| Palau | 585 | PLW |
| Papua New Guinea | 598 | PNG |
| Samoa | 882 | WSM |
| Solomon Isds | 90 | SLB |
| Tonga | 776 | TON |
| Tuvalu | 798 | TUV |
| Vanuatu | 548 | VUT |

Publication of SITC Rev. 4 annual series is incomplete for this reporter set. A diagnostic 2018–2024 extract contained observations for seven economies: Fiji, Kiribati, Palau, Papua New Guinea, Samoa, Solomon Islands, and Tonga. Absence of the remaining seven reporters in that window is treated as a publication gap, not as an API failure. Coverage for 2000–2017 is expected to remain reporter-specific.

### 3.3 Partners

**Table 4.** Requested partners

| Comtrade label | M49 | ISO3 in extract |
| --- | --- | --- |
| Australia | 36 | AUS |
| China | 156 | CHN |
| USA, Puerto Rico and US Virgin Islands | 842 | USA |
| World | 0 | W00 |

---

## 4. Authentication and API surface

### 4.1 Subscription

Requests use a Premium Institutional Pro key pair, supplied to Azure API Management as `subscription-key`. Credentials are read from the project `.env` file (excluded from version control) or from process environment variables, which take precedence:

| Variable | Role |
| --- | --- |
| `COMTRADE_PRIM_KEY` | Primary key |
| `COMTRADE_SEC_KEY` | Secondary key, used if the primary request returns no payload |

Loading is implemented in `comtrade_download/auth.py`. Credentials are not embedded in notebooks, reports, or source files.

### 4.2 Service tiers relevant to this extract

**Table 5.** Indicative service characteristics (consult current Comtrade documentation for contractual limits)

| Characteristic | Public preview | Premium synchronous data | Institutional Pro asynchronous |
| --- | --- | --- | --- |
| Client function | `previewFinalData` | `getFinalData` | `submitAsyncFinalDataRequest` |
| Typical record ceiling | 500 | 250,000 per call | approximately 2.5 million per job |
| Execution | Immediate HTTP response | Immediate HTTP response; library timeout 120 seconds | Server-side job; result posted as a file |
| Authentication | None | Subscription key | Subscription key |

Synchronous final data are requested from:

`https://comtradeapi.un.org/data/v1/get/{typeCode}/{freqCode}/{clCode}`

Asynchronous jobs are submitted to:

`https://comtradeapi.un.org/async/v1/get/{typeCode}/{freqCode}/{clCode}`

### 4.3 Library functions employed

**Table 6.** `comtradeapicall` functions used in this project

| Function | Role in the pipeline |
| --- | --- |
| `getFinalData` | Synchronous fallback extract; returns a DataFrame, or `None` on HTTP error |
| `getCountFinalData` | Optional sizing of a query; not on the default path |
| `submitAsyncFinalDataRequest` | Submits one Institutional Pro job; returns `requestId` |
| `checkAsyncDataRequest` | Polls job status and, on completion, the result URI |
| `convertCountryIso3ToCode` | Off-line code lookup during specification; not invoked at download time |

The library helper `downloadAsyncFinalDataRequest` combines submit, poll, and file save. It is not used: it reports errors by printing rather than raising, does not return a DataFrame, and does not normalize the asynchronous zip/TSV schema. Equivalent steps are implemented in `comtrade_download/client.py` and `comtrade_download/prepare.py`.

---

## 5. Retrieval strategy

### 5.1 Design objective

The pipeline must (i) obtain the full Table 1 query in a single conceptually atomic extract; (ii) remain within Premium record and timeout constraints; (iii) fail over from the primary to the secondary subscription key; and (iv) write a CSV that existing analysis loaders can ingest.

### 5.2 Control flow

The entry point is `download_pacific_sitc4_ag3` (`comtrade_download/pipeline.py`).

1. If a batch identifier is supplied, the pipeline resumes an already submitted asynchronous job.
2. Otherwise, by default, it submits the full query as one asynchronous job, polls at 15-second intervals until status `Completed` or `Error`, downloads the posted file, normalizes it, and writes CSV. Submission is retried with the secondary key if the primary key fails.
3. If asynchronous retrieval fails for both keys, the pipeline falls back to synchronous `getFinalData` calls, one reporter–year at a time, concatenates the frames, and writes the same CSV.
4. Synchronous-only execution (`use_async=False`) follows step 3 directly.

### 5.3 Preference for asynchronous retrieval

A single synchronous `getFinalData` call covering all reporters and all years, with `cmdCode='AG3'` and `breakdownMode='plus'`, did not complete within the 120-second client timeout. A diagnostic request for Fiji in 2022 returned 1,434 rows in approximately 41 seconds. A count for all fourteen reporters in 2022 returned 5,005 rows in approximately 4 seconds. The query is therefore small in output size but costly in server-side commodity expansion.

Institutional Pro asynchronous jobs are the appropriate instrument: the server accepts the full specification, processes it independently of the client timeout, and posts a downloadable archive. A diagnostic 2018–2024 request was accepted in approximately one second and completed as a zip archive. The current specification uses the same job type for 2000–2024.

### 5.4 Synchronous fallback

Should asynchronous submission be unavailable, each reporter–year is requested separately (14 × 25 = 350 calls), with a one-second pause between calls (`REQUEST_PAUSE_SECONDS`). Each call remains in the size class of the Fiji 2022 diagnostic and below the 250,000-record ceiling. Wall-clock time is substantially longer; the path exists only as a fallback. Combining all fourteen reporters in one synchronous AG3 plus-mode call is avoided because it reproduces the timeout observed in §5.3.

### 5.5 Exclusion of bulk file download

`bulkDownloadFinalFile` retrieves entire published datasets (reporter × period × classification), not the partner, flow, and commodity slice specified in Table 1. For a targeted Pacific AG3 extract, the final-data asynchronous API is the matching service family.

### 5.6 Key failover and job resumption

On HTTP failure, including unauthorized responses, `getFinalData` prints the response body and returns `None`. The client treats `None` as `ComtradeDownloadError` and retries with `COMTRADE_SEC_KEY`. Asynchronous submission uses the same key order.

If the client process stops after a successful submit, the printed batch identifier may be passed to `scripts/download_comtrade.py`. Jobs already in status `Completed` can be polled again; the lifetime of the result URI is determined by Comtrade.

---

## 6. Post-processing and schema alignment

### 6.1 Asynchronous payload

The completed job is not a camelCase JSON table. The observed artefact is:

1. an HTTPS URI to a zip archive named `batchid-<uuid>.zip`;
2. a tab-separated text member with a UTF-8 byte-order mark;
3. PascalCase headers (`TypeCode`, `RefYear`, `Cifvalue`, `PrimaryValue`);
4. unpopulated description fields, because `includeDesc` is not an asynchronous argument.

Direct `pandas.read_csv` on the zip bytes is not a valid parse of this payload.

### 6.2 Normalization

`read_extract_file` and `prepare_extract_frame` (`comtrade_download/prepare.py`) apply the following transformations:

1. decompress the archive and read the inner file as tab-separated UTF-8 with BOM;
2. convert PascalCase column names to the camelCase used by synchronous JSON (`refYear`, `cifvalue`, `primaryValue`, and so on);
3. impute missing reporter and partner labels and ISO codes from the M49 maps in Tables 3 and 4;
4. represent SITC `cmdCode` as a three-digit string (`1` → `001`);
5. write `TradeData_sitc4_ag3_2000_2024.csv`.

### 6.3 Downstream loader contract

Analysis loaders (`trade_discrepancy/loaders.py`) rename value fields and operate on the geography and flow keys below.

**Table 7.** Value-column mapping

| Extract column | Loader column |
| --- | --- |
| `cifvalue` | `cifvalue__US__` |
| `fobvalue` | `fobvalue__US__` |
| `primaryValue` | `primaryValue__US__` |

Harmonization keys remain `reporterDesc`, `refYear`, `flowCode`, and `partnerISO`. Output is written under `data/NEW COMTRADE data/`, which is excluded from version control. The discrepancy analysis loads only `TradeData_sitc4_ag3_2000_2024.csv` (`COMTRADE_FILENAME`).

---

## 7. Implementation

Retrieval is isolated in the `comtrade_download/` package and is not colocated with analysis modules (`trade_discrepancy`, `trade_influence`, `trade_anomaly`).

**Table 8.** Code organization

| Path | Responsibility |
| --- | --- |
| `comtrade_download/constants.py` | Selection criteria, geography maps, output location |
| `comtrade_download/auth.py` | Subscription-key resolution |
| `comtrade_download/query.py` | Construction of synchronous and asynchronous argument sets |
| `comtrade_download/client.py` | Synchronous and asynchronous HTTP calls |
| `comtrade_download/prepare.py` | Archive parsing, schema normalization, CSV write |
| `comtrade_download/pipeline.py` | Orchestration (`download_pacific_sitc4_ag3`) |
| `scripts/download_comtrade.py` | Command-line interface; optional batch-identifier resume |
| `tests/test_comtrade_download.py` | Filter contract, key loading, asynchronous polling, zip/TSV parse |

Operational parameters are centralized in `comtrade_download/constants.py`.

**Table 9.** Operational parameters

| Parameter | Value | Rationale |
| --- | --- | --- |
| `MAX_RECORDS` | 250,000 | Premium synchronous ceiling |
| `REQUEST_PAUSE_SECONDS` | 1.0 | Interval between synchronous fallback calls |
| `ASYNC_POLL_SECONDS` | 15.0 | Same polling interval as `comtradeapicall.Async` |
| `OUTPUT_FILENAME` | `TradeData_sitc4_ag3_2000_2024.csv` | Same file as the discrepancy loader default |
| `PERIOD_START_YEAR` | 2000 | Inclusive start of the annual range |
| `PERIOD_END_YEAR` | 2024 | Inclusive end of the annual range |
| `PERIODS` | 2000–2024 | Derived as `range(start, end + 1)` |
| `BREAKDOWN_MODE` | `plus` | Specified portal breakdown |

Changes to years, reporters, or partners are made in these constants (and in the ISO maps where new areas are added). Unit tests pin the Table 1 mapping so that unintended filter drift fails continuous integration.

---

## 8. Results of the 2000–2024 extract

The asynchronous 2000–2024 job wrote `TradeData_sitc4_ag3_2000_2024.csv` (**79,200** records). Publication does not fill the requested window. The full coverage audit is [`comtrade-api-data-characteristics-report-en.md`](comtrade-api-data-characteristics-report-en.md); the headline comparison with the earlier 2018–2024 diagnostic is:

| Dimension | Diagnostic (2018–2024) | Current extract (requested 2000–2024) |
| --- | --- | --- |
| Records | 34,405 | 79,200 |
| Years with rows | 2018–2024 | **2008–2024** (2000–2007 empty) |
| Flows | `M`, `X` | `M`, `X` |
| Partners | `AUS`, `CHN`, `USA`, `W00` | `AUS`, `CHN`, `USA`, `W00` |
| Reporters with at least one row | Fiji, Kiribati, Palau, Papua New Guinea, Samoa, Solomon Isds, Tonga | Same seven, plus **Cook Islands** (2008 exports only) |
| Reporters in the request with no rows | Cook Isds, FS Micronesia, Marshall Isds, Nauru, Niue, Tuvalu, Vanuatu | FS Micronesia, Marshall Isds, Nauru, Niue, Tuvalu, Vanuatu |

Of 14 × 25 = 350 requested reporter–years, **70** (20%) contain data. Peak coverage is six reporters in 2017–2018. Fiji is the only unbroken 2008–2024 series.

---

## 9. Reproduction

From the project root:

```bash
poetry run python scripts/download_comtrade.py
```

To resume a previously accepted job:

```bash
poetry run python scripts/download_comtrade.py <batch-id>
```

Programmatic entry point:

```python
from comtrade_download import download_pacific_sitc4_ag3

path, frame = download_pacific_sitc4_ag3()
```

---

## References

UN Comtrade. (n.d.). *UN Comtrade Help Center*. <https://uncomtrade.org/docs>

UN Comtrade. (n.d.). *Comtrade Plus*. <https://comtradeplus.un.org>

UN Comtrade. (n.d.). *comtradeapicall* [Python library]. <https://github.com/uncomtrade/comtradeapicall>
