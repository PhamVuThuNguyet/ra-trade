"use client";

import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import { Chart } from "react-chartjs-2";

import type { OverlayBundle, Partner, PartnerId } from "../lib/catalog";
import {
  AID_AXIS_ID,
  AID_AXIS_TITLE,
  TONE_AXIS_ID,
  TONE_AXIS_TITLE,
  overlayAidBarDatasets,
  overlayAnnotations,
  overlayNotesForYear,
  overlayToneLineDatasets,
} from "../lib/chart-overlay";
import { LINE_STYLE, partnerColor, partnerLabel } from "../lib/colors";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  BarElement,
  BarController,
  Tooltip,
  Legend,
  annotationPlugin,
);

const PARTNER_ORDER = ["aus", "china", "us"] as const;
const LINE_DATASET_ORDER = 1;
const OVERLAY_TOP_PADDING = 36;

type PlotPoint = {
  year: number;
  partner: PartnerId;
  value: number | null;
};

type Props = {
  title: string;
  seriesId: string;
  points: PlotPoint[];
  partners: Partner[];
  overlay: OverlayBundle | null;
  valueLabel: string;
};

export function IndexPlot({ title, seriesId, points, partners, overlay, valueLabel }: Props) {
  const years = [...new Set(points.map((point) => point.year))].sort((a, b) => a - b);
  if (years.length === 0) {
    return (
      <article className="plot-card">
        <h3>{title}</h3>
        <p className="muted">No values for {title} in this selection.</p>
      </article>
    );
  }

  const lineDatasets = PARTNER_ORDER.map((partnerId) => ({
    type: "line" as const,
    label: partnerLabel(partners, partnerId),
    yAxisID: "y",
    order: LINE_DATASET_ORDER,
    data: years.map((year) => {
      const match = points.find((point) => point.partner === partnerId && point.year === year);
      return match?.value ?? null;
    }),
    borderColor: partnerColor(partners, partnerId),
    backgroundColor: partnerColor(partners, partnerId),
    borderDash: LINE_STYLE === "solid" ? [] : [6, 4],
    tension: 0.05,
    pointRadius: 2,
    borderWidth: 2,
  }));
  const aidDatasets = overlay ? overlayAidBarDatasets(overlay, years, partners) : [];
  const toneDatasets = overlay ? overlayToneLineDatasets(overlay, years, partners) : [];
  const showAidAxis = aidDatasets.length > 0;
  const showToneAxis = toneDatasets.length > 0;

  return (
    <article className="plot-card" data-series={seriesId}>
      <h3>{title}</h3>
      <Chart
        type="bar"
        data={{
          labels: years.map(String),
          datasets: [...aidDatasets, ...toneDatasets, ...lineDatasets],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            annotation: overlay
              ? { annotations: overlayAnnotations(overlay, years) }
              : { annotations: {} },
            tooltip: {
              callbacks: {
                afterBody: (items) => {
                  if (!overlay) {
                    return [];
                  }
                  const year = years[items[0]?.dataIndex ?? 0];
                  return overlayNotesForYear(overlay, year);
                },
              },
            },
          },
          scales: {
            y: {
              type: "linear",
              title: { display: true, text: valueLabel },
              grid: { color: "rgba(0,0,0,0.06)" },
            },
            [AID_AXIS_ID]: {
              type: "linear",
              position: "right",
              display: showAidAxis,
              beginAtZero: true,
              title: { display: showAidAxis, text: AID_AXIS_TITLE },
              grid: { drawOnChartArea: false },
            },
            [TONE_AXIS_ID]: {
              type: "linear",
              position: "right",
              display: showToneAxis,
              title: { display: showToneAxis, text: TONE_AXIS_TITLE },
              grid: { drawOnChartArea: false },
            },
            x: { grid: { display: false } },
          },
          layout: overlay ? { padding: { top: OVERLAY_TOP_PADDING, right: 8 } } : undefined,
        }}
      />
    </article>
  );
}
