"""Build comtradeapicall selection-criteria kwargs."""

from collections.abc import Mapping, Sequence

from comtrade_download.constants import (
    ASYNC_KWARG_NAMES,
    BREAKDOWN_MODE,
    CLASSIFICATION_CODE,
    CMD_CODE,
    CUSTOMS_CODE,
    FLOW_CODE,
    FREQ_CODE,
    MAX_RECORDS,
    MOT_CODE,
    PARTNER2_CODE,
    PARTNER_CODES,
    PERIODS,
    REPORTER_CODES,
    TYPE_CODE,
)


def joined_codes(codes: Mapping[str, str]) -> str:
    return ",".join(codes.values())


def final_data_kwargs(
    period: str,
    reporter_code: str | None = None,
    partner_code: str | None = None,
) -> dict[str, object]:
    return {
        "typeCode": TYPE_CODE,
        "freqCode": FREQ_CODE,
        "clCode": CLASSIFICATION_CODE,
        "period": period,
        "reporterCode": reporter_code or joined_codes(REPORTER_CODES),
        "cmdCode": CMD_CODE,
        "flowCode": FLOW_CODE,
        "partnerCode": partner_code or joined_codes(PARTNER_CODES),
        "partner2Code": PARTNER2_CODE,
        "customsCode": CUSTOMS_CODE,
        "motCode": MOT_CODE,
        "maxRecords": MAX_RECORDS,
        "format_output": "JSON",
        "aggregateBy": None,
        "breakdownMode": BREAKDOWN_MODE,
        "countOnly": None,
        "includeDesc": True,
    }


def async_request_kwargs(periods: Sequence[str] = PERIODS) -> dict[str, object]:
    kwargs = final_data_kwargs(",".join(periods))
    return {name: kwargs[name] for name in ASYNC_KWARG_NAMES}
