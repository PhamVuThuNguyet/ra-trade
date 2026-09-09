"use client";

import { useEffect, useMemo, useState } from "react";

import type {
  DataTypeId,
  ExplorerCatalog,
  PartnerId,
  ProductGroupId,
  SourceId,
} from "../lib/catalog";
import { filterRows } from "../lib/filters";
import { missingOverlayNotes, overlayForReporter } from "../lib/overlay";
import {
  filterPlotSeries,
  goodsPlotIdsForProductGroup,
  GOODS_PLOT_IDS,
  uniqueCountries,
} from "../lib/plot-indices";
import { labeledProductGroups } from "../lib/product-groups";
import { DataTable } from "./DataTable";
import { EmptyState } from "./EmptyState";
import { FilterBar } from "./FilterBar";
import { PlotGrid } from "./PlotGrid";
import { SourceTypeControls } from "./SourceTypeControls";

export function ExplorerApp() {
  const [catalog, setCatalog] = useState<ExplorerCatalog | null>(null);
  const [loadError, setLoadError] = useState("");
  const [sourceId, setSourceId] = useState<SourceId>("baci");
  const [dataTypeId, setDataTypeId] = useState<DataTypeId>("goods_trade");
  const [viewMode, setViewMode] = useState<"table" | "plot">("table");
  const [reporter, setReporter] = useState("");
  const [yearMin, setYearMin] = useState("");
  const [yearMax, setYearMax] = useState("");
  const [productGroupId, setProductGroupId] = useState<ProductGroupId>("all_products");

  useEffect(() => {
    fetch("data/catalog.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("missing");
        }
        return response.json();
      })
      .then((payload: ExplorerCatalog) => {
        setCatalog(payload);
        const countries = uniqueCountries(payload.index_series, "baci");
        if (countries[0]) {
          setReporter(countries[0]);
        }
      })
      .catch(() => setLoadError("expected path data/catalog.json"));
  }, []);

  const table = useMemo(() => {
    if (!catalog) {
      return null;
    }
    return (
      catalog.tables.find(
        (item) =>
          item.source_id === sourceId &&
          item.data_type_id === dataTypeId &&
          item.product_group_id === productGroupId,
      ) ?? null
    );
  }, [catalog, sourceId, dataTypeId, productGroupId]);

  const reporters = useMemo(() => {
    if (!catalog) {
      return [];
    }
    if (dataTypeId === "services") {
      const rows =
        catalog.tables.find(
          (item) =>
            item.source_id === sourceId &&
            item.data_type_id === "services" &&
            item.product_group_id === "all_products",
        )?.rows ?? [];
      return [...new Set(rows.map((row) => String(row.country)))].sort();
    }
    return uniqueCountries(catalog.index_series, sourceId);
  }, [catalog, sourceId, dataTypeId]);

  useEffect(() => {
    if (reporters.length === 0) {
      return;
    }
    if (reporter && reporters.includes(reporter)) {
      return;
    }
    setReporter(reporters[0]);
  }, [reporters, reporter]);

  if (loadError) {
    return <EmptyState title="Catalog missing" detail={loadError} />;
  }
  if (!catalog) {
    return <p className="muted">Loading catalog…</p>;
  }

  const source = catalog.sources.find((item) => item.id === sourceId);
  const yearMinNum = yearMin === "" ? null : Number(yearMin);
  const yearMaxNum = yearMax === "" ? null : Number(yearMax);
  const tableRows = filterRows(table?.rows ?? [], {
    reporters: reporter ? [reporter] : undefined,
    yearMin: Number.isFinite(yearMinNum) ? yearMinNum : null,
    yearMax: Number.isFinite(yearMaxNum) ? yearMaxNum : null,
  });

  const catalogIndexIds =
    catalog.ui.goods_trade_index_ids.length > 0 ? catalog.ui.goods_trade_index_ids : GOODS_PLOT_IDS;
  const goodsIndexIds = goodsPlotIdsForProductGroup(productGroupId, catalogIndexIds);
  const plotSeries = filterPlotSeries(
    catalog.index_series,
    sourceId,
    reporter,
    yearMinNum,
    yearMaxNum,
    goodsIndexIds,
  );
  const plotOverlay = overlayForReporter(catalog.overlay, reporter);
  const overlayNotes = missingOverlayNotes(catalog.overlay);
  const goodsPlots = goodsIndexIds.map((indexId) => ({
    id: indexId,
    title: catalog.index_display[indexId],
    points: plotSeries
      .filter((point) => point.index_id === indexId)
      .map((point) => ({ year: point.year, partner: point.partner, value: point.value })),
  }));
  const servicePlots = servicePlotSpecs(table?.rows ?? [], reporter, yearMinNum, yearMaxNum);
  const emptyDetail = emptyCombinationDetail(
    source?.display_name ?? sourceId,
    dataTypeId,
    productGroupId,
    reporter,
    yearMin,
    yearMax,
  );

  return (
    <main className={viewMode === "plot" ? "page page-plots" : "page"}>
      <SourceTypeControls
        sourceId={sourceId}
        dataTypeId={dataTypeId}
        sources={catalog.sources}
        dataTypes={catalog.data_types}
        onSource={setSourceId}
        onDataType={setDataTypeId}
        viewMode={viewMode}
        onViewMode={setViewMode}
      />
      <FilterBar
        reporters={reporters}
        selectedReporter={reporter}
        onReporter={setReporter}
        yearMin={yearMin}
        yearMax={yearMax}
        onYearMin={setYearMin}
        onYearMax={setYearMax}
        productGroupId={productGroupId}
        productGroups={labeledProductGroups(catalog.product_groups, dataTypeId)}
        onProductGroup={setProductGroupId}
      />
      {overlayNotes.length > 0 && viewMode === "plot" && dataTypeId === "goods_trade" ? (
        <p className="banner warn">{overlayNotes.join(" · ")}</p>
      ) : null}

      {viewMode === "table" ? (
        tableRows.length === 0 ? (
          <EmptyState title="No rows" detail={emptyDetail} />
        ) : (
          <DataTable columns={table?.columns ?? []} rows={tableRows} />
        )
      ) : !reporter ? (
        <EmptyState title="PIC required" detail="Select a reporter (PIC) to draw the plots." />
      ) : dataTypeId === "services" ? (
        servicePlots.length === 0 ? (
          <EmptyState title="No services plot" detail={emptyDetail} />
        ) : (
          <PlotGrid
            plots={servicePlots}
            partners={catalog.partners}
            overlay={null}
            valueLabel="USD (mock)"
          />
        )
      ) : (
        <PlotGrid
          plots={goodsPlots}
          partners={catalog.partners}
          overlay={plotOverlay}
          valueLabel="Index"
        />
      )}
    </main>
  );
}

function emptyCombinationDetail(
  sourceName: string,
  dataTypeId: DataTypeId,
  productGroupId: ProductGroupId,
  reporter: string,
  yearMin: string,
  yearMax: string,
): string {
  const pic = reporter ? `, ${reporter}` : "";
  const years = yearMin || yearMax ? `, years ${yearMin}–${yearMax}` : "";
  return `No rows for ${sourceName}, ${dataTypeId}, ${productGroupId}${pic}${years}.`;
}

function servicePlotSpecs(
  rows: Record<string, unknown>[],
  reporter: string,
  yearMin: number | null,
  yearMax: number | null,
): { id: string; title: string; points: { year: number; partner: PartnerId; value: number | null }[] }[] {
  const filtered = rows.filter((row) => {
    if (reporter && String(row.country) !== reporter) {
      return false;
    }
    const year = Number(row.year);
    if (yearMin != null && Number.isFinite(yearMin) && year < yearMin) {
      return false;
    }
    if (yearMax != null && Number.isFinite(yearMax) && year > yearMax) {
      return false;
    }
    return true;
  });
  const categories = [...new Set(filtered.map((row) => String(row.service_category ?? "")))].filter(
    Boolean,
  );
  return categories.map((category) => ({
    id: category.toLowerCase(),
    title: category,
    points: filtered
      .filter((row) => String(row.service_category) === category)
      .map((row) => ({
        year: Number(row.year),
        partner: row.partner as PartnerId,
        value: row.value_usd == null ? null : Number(row.value_usd),
      })),
  }));
}
