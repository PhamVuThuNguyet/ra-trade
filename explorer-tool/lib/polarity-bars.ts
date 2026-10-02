import type { OverlayBundle, Partner, PartnerId } from "./catalog";
import { colorWithAlpha, partnerColor, partnerLabel } from "./colors";

export const POLARITY_AXIS_ID = "yPolarity";
export const POLARITY_AXIS_TITLE = "GKG items";

const PARTNER_ORDER: PartnerId[] = ["aus", "china", "us"];
const POLARITY_DATASET_ORDER = 0;
const SHADE = {
  negative: 0.95,
  neutral: 0.55,
  positive: 0.28,
} as const;

export type PolarityBarDataset = {
  type: "bar";
  label: string;
  yAxisID: string;
  order: number;
  stack: string;
  data: Array<number | null>;
  backgroundColor: string;
  borderColor: string;
  borderWidth: number;
  maxBarThickness: number;
};

export function overlayPolarityBarDatasets(
  overlay: OverlayBundle,
  years: number[],
  partners: Partner[],
): PolarityBarDataset[] {
  if (overlay.sentiment_status !== "present") {
    return [];
  }
  const datasets: PolarityBarDataset[] = [];
  for (const partnerId of PARTNER_ORDER) {
    const color = partnerColor(partners, partnerId);
    const label = partnerLabel(partners, partnerId);
    const segments = (
      [
        ["negative", "negative", SHADE.negative],
        ["neutral", "neutral", SHADE.neutral],
        ["positive", "positive", SHADE.positive],
      ] as const
    ).map(([key, name, alpha]) => ({
      type: "bar" as const,
      label: `${label} ${name}`,
      yAxisID: POLARITY_AXIS_ID,
      order: POLARITY_DATASET_ORDER,
      stack: partnerId,
      data: years.map((year) => polarityCount(overlay, partnerId, year, key)),
      backgroundColor: colorWithAlpha(color, alpha),
      borderColor: color,
      borderWidth: 0,
      maxBarThickness: 12,
    }));
    if (segments.some((segment) => segment.data.some((value) => value != null && value > 0))) {
      datasets.push(...segments);
    }
  }
  return datasets;
}

function polarityCount(
  overlay: OverlayBundle,
  partnerId: PartnerId,
  year: number,
  key: "negative" | "neutral" | "positive",
): number | null {
  const match = (overlay.sentiment ?? []).find(
    (point) => point.partner === partnerId && point.year === year,
  );
  if (!match) {
    return null;
  }
  const negative = match.n_negative ?? 0;
  const neutral = match.n_neutral ?? 0;
  const positive = match.n_positive ?? 0;
  if (negative + neutral + positive <= 0) {
    return null;
  }
  if (key === "negative") {
    return negative;
  }
  if (key === "neutral") {
    return neutral;
  }
  return positive;
}
