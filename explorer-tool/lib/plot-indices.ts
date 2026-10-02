import type { DataTypeId, IndexId, IndexPoint, ProductGroupId, SourceId } from "./catalog";

export const GOODS_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "scti",
  "cwi",
  "cwe",
  "cwti",
  "cweii",
  "eiti",
];

const ALL_PRODUCTS_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "scti",
  "cwi",
  "cwe",
  "cwti",
  "eiti",
];

const ESSENTIAL_PLOT_IDS: IndexId[] = ["cweii"];

const SERVICE_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "scti",
  "cwi",
  "cwe",
  "cwti",
  "eiti",
];

export function goodsPlotIdsForProductGroup(
  productGroupId: ProductGroupId,
  catalogIds: IndexId[] = GOODS_PLOT_IDS,
  dataTypeId: DataTypeId = "goods_trade",
): IndexId[] {
  const wanted =
    dataTypeId === "services"
      ? SERVICE_PLOT_IDS
      : productGroupId === "essential_commodities"
        ? ESSENTIAL_PLOT_IDS
        : ALL_PRODUCTS_PLOT_IDS;
  const wantedSet = new Set(wanted);
  const fromCatalog = catalogIds.filter((id) => wantedSet.has(id));
  return fromCatalog.length > 0 ? fromCatalog : [...wanted];
}

export function uniqueCountries(series: IndexPoint[], sourceId: SourceId): string[] {
  return [
    ...new Set(series.filter((point) => point.source_id === sourceId).map((point) => point.country)),
  ].sort();
}

export function filterPlotSeries(
  series: IndexPoint[],
  sourceId: SourceId,
  reporter: string,
  yearMin: number | null,
  yearMax: number | null,
  indexIds: IndexId[],
): IndexPoint[] {
  const allowed = new Set(indexIds);
  return series.filter((point) => {
    if (point.source_id !== sourceId || point.country !== reporter) {
      return false;
    }
    if (!allowed.has(point.index_id)) {
      return false;
    }
    if (yearMin != null && Number.isFinite(yearMin) && point.year < yearMin) {
      return false;
    }
    if (yearMax != null && Number.isFinite(yearMax) && point.year > yearMax) {
      return false;
    }
    return true;
  });
}
