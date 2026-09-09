import type { Partner, PartnerId } from "./catalog";

export const LINE_STYLE = "solid" as const;

export function partnerColor(partners: Partner[], partnerId: PartnerId): string {
  const match = partners.find((partner) => partner.id === partnerId);
  return match?.plot_color ?? "#333333";
}

export function partnerLabel(partners: Partner[], partnerId: PartnerId): string {
  const match = partners.find((partner) => partner.id === partnerId);
  return match?.display_name ?? partnerId;
}

const HEX_RGB = /^#?([0-9a-fA-F]{6})$/;

export function colorWithAlpha(hex: string, alpha: number): string {
  const match = HEX_RGB.exec(hex.trim());
  if (!match) {
    return hex;
  }
  const value = match[1];
  const red = Number.parseInt(value.slice(0, 2), 16);
  const green = Number.parseInt(value.slice(2, 4), 16);
  const blue = Number.parseInt(value.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
