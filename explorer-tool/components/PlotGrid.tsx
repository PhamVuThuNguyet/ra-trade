"use client";

import type { OverlayBundle, Partner } from "../lib/catalog";
import { IndexPlot } from "./IndexPlot";
import { OverlayLegend } from "./OverlayLegend";

export type PlotSpec = {
  id: string;
  title: string;
  points: { year: number; partner: "aus" | "china" | "us"; value: number | null }[];
};

type Props = {
  plots: PlotSpec[];
  partners: Partner[];
  overlay: OverlayBundle | null;
  valueLabel: string;
};

export function PlotGrid({ plots, partners, overlay, valueLabel }: Props) {
  return (
    <div className="plot-full-width">
      <OverlayLegend overlay={overlay} />
      <div className="plot-grid">
        {plots.map((plot) => (
          <IndexPlot
            key={plot.id}
            seriesId={plot.id}
            title={plot.title}
            points={plot.points}
            partners={partners}
            overlay={overlay}
            valueLabel={valueLabel}
          />
        ))}
      </div>
    </div>
  );
}
