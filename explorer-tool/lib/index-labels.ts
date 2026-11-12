import type { DataTypeId } from "./catalog";

const GOODS_PLOT_TITLES: Record<string, string> = {
  import_index: "Simple commodity import index (SCII)",
  export_index: "Simple commodity export index (SCEI)",
  scti: "Simple commodity trade index (SCTI)",
  cwi: "Commodity-weighted import index (CWII)",
  cwe: "Commodity-weighted export index (CWEI)",
  cwti: "Commodity-weighted trade index (CWTI)",
  cweii: "Commodity-weighted essential import index (CWEII)",
  eiti: "Economic influence trade index (EITI)",
};

const SERVICE_PLOT_TITLES: Record<string, string> = {
  import_index: "Simple services import index (SSII)",
  export_index: "Simple services export index (SSEI)",
  scti: "Simple services trade index (SSTI)",
  cwi: "Services-weighted import index (SWII)",
  cwe: "Services-weighted export index (SWEI)",
  cwti: "Services-weighted trade index (SWTI)",
  eiti: "Economic influence trade index (EITI)",
};

export function expandedPlotTitle(
  indexId: string,
  dataTypeId: DataTypeId,
  fallback: string,
): string {
  const labels = dataTypeId === "services" ? SERVICE_PLOT_TITLES : GOODS_PLOT_TITLES;
  return labels[indexId] ?? fallback;
}
