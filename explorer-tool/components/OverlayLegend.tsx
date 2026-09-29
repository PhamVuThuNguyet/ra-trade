"use client";

import type { OverlayBundle } from "../lib/catalog";

type Props = {
  overlay: OverlayBundle | null;
  showPartners?: boolean;
};

export function OverlayLegend({ overlay, showPartners = true }: Props) {
  return (
    <ul className="overlay-legend" aria-label="Plot key">
      {showPartners ? (
        <>
          <li>
            <span className="swatch line aus" /> Australia
          </li>
          <li>
            <span className="swatch line china" /> China
          </li>
          <li>
            <span className="swatch line us" /> United States
          </li>
        </>
      ) : null}
      {overlay ? (
        <>
          <li>
            <span className="swatch band disaster" /> Disaster year
          </li>
          <li>
            <span className="swatch band span" /> COVID / GFC / RAMSI
          </li>
          <li>
            <span className="swatch dash" /> Calendar event
          </li>
          {overlay.aid_status === "present" ? (
            <li>
              <span className="swatch bar" /> Lowy aid (spent)
            </li>
          ) : null}
          {overlay.sentiment_status === "present" ? (
            <li>
              <span className="swatch tone" /> GDELT tone (n≥5)
            </li>
          ) : null}
        </>
      ) : null}
    </ul>
  );
}
