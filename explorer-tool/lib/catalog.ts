export type PartnerId = "aus" | "china" | "us";
export type SourceId = "baci" | "comtrade" | "batis";
export type DataTypeId = "goods_trade" | "services";
export type ProductGroupId = "all_products" | "essential_commodities";
export type IndexId =
  | "import_index"
  | "export_index"
  | "scti"
  | "cwi"
  | "cwe"
  | "cwti"
  | "cweii"
  | "eiti";
export type ProvenanceKind = "study_output" | "mock";
export type OverlayStatus = "present" | "missing";

export type Partner = {
  id: PartnerId;
  display_name: string;
  plot_color: string;
};

export type IndexPoint = {
  source_id: SourceId;
  country: string;
  year: number;
  partner: PartnerId;
  index_id: IndexId;
  value: number | null;
  provenance: ProvenanceKind;
};

export type CatalogTable = {
  source_id: SourceId;
  data_type_id: DataTypeId;
  product_group_id: ProductGroupId;
  provenance: ProvenanceKind;
  vintage: string | null;
  columns: string[];
  rows: Record<string, unknown>[];
};

export type CalendarMark = {
  event_id: string;
  year_start: number;
  year_end: number;
  country: string;
  partner: PartnerId | "*";
  event_type: string;
  title: string;
  encoding: "span" | "line";
};

export type AidPoint = {
  country: string;
  year: number;
  partner: PartnerId;
  lowy_spent_usd: number | null;
};

export type DisasterYear = {
  country: string;
  year: number;
  emdat_has_disaster: 0 | 1;
  emdat_n_events?: number;
};

export type SentimentPoint = {
  country: string;
  year: number;
  partner: PartnerId;
  n_items: number;
  n_with_tone: number;
  mean_tone: number | null;
  n_positive: number;
  n_neutral: number;
  n_negative: number;
};

export type OverlayBundle = {
  calendar_status: OverlayStatus;
  aid_status: OverlayStatus;
  disaster_status: OverlayStatus;
  sentiment_status: OverlayStatus;
  calendar: CalendarMark[];
  aid: AidPoint[];
  disasters: DisasterYear[];
  sentiment: SentimentPoint[];
};

export type ExplorerCatalog = {
  generated_from: {
    note: string;
    baci_vintage: string | null;
    comtrade_vintage: string | null;
    batis_vintage?: string | null;
  };
  sources: { id: SourceId; display_name: string; vintage: string | null }[];
  data_types: {
    id: DataTypeId;
    display_name: string;
    provenance_default: ProvenanceKind;
  }[];
  product_groups: { id: ProductGroupId; display_name: string }[];
  partners: Partner[];
  index_display: Record<string, string>;
  service_index_display?: Record<string, string>;
  ui: {
    partner_filter: false;
    index_toggles: false;
    goods_trade_index_ids: IndexId[];
  };
  essential_divisions: {
    code: string;
    description: string;
    purpose: string;
  }[];
  tables: CatalogTable[];
  index_series: IndexPoint[];
  overlay: OverlayBundle;
};
