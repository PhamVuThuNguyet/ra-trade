import type { OverlayBundle, PartnerId } from "./catalog";

export function overlayForReporter(
  overlay: OverlayBundle,
  reporter: string,
): OverlayBundle {
  return {
    ...overlay,
    calendar: overlay.calendar.filter(
      (event) => event.country === reporter || event.country === "*",
    ),
    aid: overlay.aid.filter((point) => point.country === reporter),
    disasters: overlay.disasters.filter((row) => row.country === reporter),
    sentiment: (overlay.sentiment ?? []).filter((point) => point.country === reporter),
  };
}

export function partnerApplies(
  eventPartner: PartnerId | "*",
  partner: PartnerId,
): boolean {
  return eventPartner === "*" || eventPartner === partner;
}

export function missingOverlayNotes(overlay: OverlayBundle): string[] {
  const notes: string[] = [];
  if (overlay.calendar_status === "missing") {
    notes.push("Calendar overlay missing");
  }
  if (overlay.aid_status === "missing") {
    notes.push("Lowy aid overlay missing");
  }
  if (overlay.disaster_status === "missing") {
    notes.push("EM-DAT overlay missing");
  }
  if (overlay.sentiment_status === "missing") {
    notes.push("GDELT tone overlay missing");
  }
  return notes;
}
