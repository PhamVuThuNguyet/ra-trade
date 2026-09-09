import type { IndexId, IndexPoint, ProductGroupId, SourceId } from "./catalog";

export const GOODS_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "cwi",
  "cwe",
  "cwi_essential",
  "cwe_essential",
];

const ALL_PRODUCTS_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "cwi",
  "cwe",
];

const ESSENTIAL_PLOT_IDS: IndexId[] = [
  "import_index",
  "export_index",
  "cwi_essential",
  "cwe_essential",
];

export function goodsPlotIdsForProductGroup(
  productGroupId: ProductGroupId,
  catalogIds: IndexId[] = GOODS_PLOT_IDS,
): IndexId[] {
  const wanted =
    productGroupId === "essential_commodities" ? ESSENTIAL_PLOT_IDS : ALL_PRODUCTS_PLOT_IDS;
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
