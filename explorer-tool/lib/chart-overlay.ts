import type { AnnotationOptions } from "chartjs-plugin-annotation";

import type { OverlayBundle, Partner, PartnerId } from "./catalog";
import { colorWithAlpha, partnerColor, partnerLabel } from "./colors";

const DISASTER_FILL = "rgba(244, 211, 94, 0.16)";
const SPAN_FILL = "rgba(120, 120, 120, 0.10)";
const CALENDAR_LINE = "#6b6560";
const CALENDAR_LABEL_MAX = 22;
const CALENDAR_LABEL_OFFSET_PX = 10;
const CALENDAR_LABEL_ROTATION_DEG = 270;
const AID_BAR_ALPHA = 0.35;
const AID_DATASET_ORDER = 0;
export const AID_AXIS_ID = "yAid";
export const AID_AXIS_TITLE = "Lowy aid (USD)";
export const TONE_AXIS_ID = "yTone";
export const TONE_AXIS_TITLE = "GDELT tone";
export const TONE_MIN_N = 5;
const TONE_DATASET_ORDER = 2;

const PARTNER_ORDER: PartnerId[] = ["aus", "china", "us"];

export function overlayAnnotations(
  overlay: OverlayBundle,
  years: number[],
): Record<string, AnnotationOptions> {
  const annotations: Record<string, AnnotationOptions> = {};
  const yearIndex = new Map(years.map((year, index) => [year, index]));

  mergeYearRuns(
    overlay.disasters.filter((row) => row.emdat_has_disaster === 1).map((row) => row.year),
  ).forEach(([startYear, endYear], index) => {
    const start = yearIndex.get(startYear);
    const end = yearIndex.get(endYear) ?? start;
    if (start === undefined || end === undefined) {
      return;
    }
    annotations[`disaster-${index}`] = {
      type: "box",
      xMin: start - 0.4,
      xMax: end + 0.4,
      backgroundColor: DISASTER_FILL,
      borderWidth: 0,
    };
  });

  uniqueSpans(overlay).forEach((span, index) => {
    const start = yearIndex.get(span.start);
    const end = yearIndex.get(span.end) ?? start;
    if (start === undefined || end === undefined) {
      return;
    }
    annotations[`span-${index}`] = {
      type: "box",
      xMin: start - 0.4,
      xMax: end + 0.4,
      backgroundColor: SPAN_FILL,
      borderWidth: 0,
    };
  });

  uniquePointEvents(overlay).forEach((event, index) => {
    const x = yearIndex.get(event.year);
    if (x === undefined) {
      return;
    }
    annotations[`event-${index}`] = {
      type: "line",
      xMin: x,
      xMax: x,
      borderColor: CALENDAR_LINE,
      borderDash: [5, 4],
      borderWidth: 1,
      label: {
        display: Boolean(event.title),
        content: event.title,
        rotation: CALENDAR_LABEL_ROTATION_DEG,
        position: "start",
        xAdjust: CALENDAR_LABEL_OFFSET_PX,
        yAdjust: 0,
        color: CALENDAR_LINE,
        backgroundColor: "rgba(255, 252, 247, 0.86)",
        borderWidth: 0,
        padding: 3,
        font: { size: 10, weight: "normal" },
      },
    };
  });

  return annotations;
}

export type AidBarDataset = {
  type: "bar";
  label: string;
  yAxisID: string;
  order: number;
  data: Array<number | null>;
  backgroundColor: string;
  borderWidth: number;
};

export function overlayAidBarDatasets(
  overlay: OverlayBundle,
  years: number[],
  partners: Partner[],
): AidBarDataset[] {
  if (overlay.aid_status !== "present") {
    return [];
  }
  const datasets = PARTNER_ORDER.map((partnerId) => ({
    type: "bar" as const,
    label: `Lowy aid (${partnerLabel(partners, partnerId)})`,
    yAxisID: AID_AXIS_ID,
    order: AID_DATASET_ORDER,
    data: years.map((year) => aidSpentForYear(overlay, partnerId, year)),
    backgroundColor: colorWithAlpha(partnerColor(partners, partnerId), AID_BAR_ALPHA),
    borderWidth: 0,
  }));
  return datasets.filter((dataset) => dataset.data.some((value) => value != null));
}

export function overlayNotesForYear(overlay: OverlayBundle, year: number): string[] {
  const notes: string[] = [];
  const titles = [
    ...new Set(
      overlay.calendar
        .filter((event) => year >= event.year_start && year <= event.year_end)
        .map((event) => event.title),
    ),
  ];
  notes.push(...titles);
  if (overlay.disasters.some((row) => row.year === year && row.emdat_has_disaster === 1)) {
    notes.push("Disaster year");
  }
  if (overlay.aid.some((point) => point.year === year && (point.lowy_spent_usd ?? 0) > 0)) {
    notes.push("Lowy aid");
  }
  notes.push(...toneNotesForYear(overlay, year));
  return notes;
}

const TONE_PARTNER_LABEL: Record<PartnerId, string> = {
  aus: "Australia",
  china: "China",
  us: "United States",
};

export function overlayToneLineDatasets(
  overlay: OverlayBundle,
  years: number[],
  partners: Partner[],
) {
  if (overlay.sentiment_status !== "present") {
    return [];
  }
  const datasets = PARTNER_ORDER.map((partnerId) => ({
    type: "line" as const,
    label: `GDELT tone (${partnerLabel(partners, partnerId)})`,
    yAxisID: TONE_AXIS_ID,
    order: TONE_DATASET_ORDER,
    data: years.map((year) => toneForPlot(overlay, partnerId, year)),
    borderColor: partnerColor(partners, partnerId),
    backgroundColor: partnerColor(partners, partnerId),
    borderDash: [5, 4],
    pointStyle: "rect" as const,
    pointRadius: 3,
    borderWidth: 1.6,
    spanGaps: false,
  }));
  return datasets.filter((dataset) => dataset.data.some((value) => value != null));
}

function toneForPlot(
  overlay: OverlayBundle,
  partnerId: PartnerId,
  year: number,
): number | null {
  const match = (overlay.sentiment ?? []).find(
    (point) => point.partner === partnerId && point.year === year,
  );
  if (!match || match.mean_tone == null || match.n_with_tone < TONE_MIN_N) {
    return null;
  }
  return match.mean_tone;
}

function toneNotesForYear(overlay: OverlayBundle, year: number): string[] {
  return (overlay.sentiment ?? [])
    .filter((point) => point.year === year && point.mean_tone != null)
    .map(
      (point) =>
        `${TONE_PARTNER_LABEL[point.partner]} tone ${point.mean_tone?.toFixed(2)} (n=${point.n_with_tone})`,
    );
}

function aidSpentForYear(
  overlay: OverlayBundle,
  partnerId: PartnerId,
  year: number,
): number | null {
  const match = overlay.aid.find((point) => point.partner === partnerId && point.year === year);
  const spent = match?.lowy_spent_usd;
  if (spent == null || spent <= 0) {
    return null;
  }
  return spent;
}

function mergeYearRuns(years: number[]): [number, number][] {
  const unique = [...new Set(years)].sort((a, b) => a - b);
  if (unique.length === 0) {
    return [];
  }
  const runs: [number, number][] = [];
  let start = unique[0];
  let prev = unique[0];
  for (const year of unique.slice(1)) {
    if (year === prev + 1) {
      prev = year;
      continue;
    }
    runs.push([start, prev]);
    start = year;
    prev = year;
  }
  runs.push([start, prev]);
  return runs;
}

function uniqueSpans(overlay: OverlayBundle): { start: number; end: number }[] {
  const byType = new Map<string, { start: number; end: number }>();
  for (const event of overlay.calendar) {
    if (event.encoding !== "span") {
      continue;
    }
    const current = byType.get(event.event_type);
    if (!current) {
      byType.set(event.event_type, { start: event.year_start, end: event.year_end });
      continue;
    }
    current.start = Math.min(current.start, event.year_start);
    current.end = Math.max(current.end, event.year_end);
  }
  return [...byType.values()];
}

function uniquePointEvents(overlay: OverlayBundle): { year: number; title: string }[] {
  const byYear = new Map<number, string[]>();
  for (const event of overlay.calendar) {
    if (event.encoding !== "line") {
      continue;
    }
    const titles = byYear.get(event.year_start) ?? [];
    const title = event.title.trim();
    if (title && !titles.includes(title)) {
      titles.push(title);
    }
    byYear.set(event.year_start, titles);
  }
  return [...byYear.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([year, titles]) => ({
      year,
      title: shortenCalendarTitle(titles[0] ?? ""),
    }));
}

function shortenCalendarTitle(title: string): string {
  if (title.length <= CALENDAR_LABEL_MAX) {
    return title;
  }
  return `${title.slice(0, CALENDAR_LABEL_MAX - 1)}…`;
}
