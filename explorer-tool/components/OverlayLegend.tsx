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
            <span className="swatch band span" /> COVID-19 / global financial crisis / Regional Assistance Mission to Solomon Islands
          </li>
          <li>
            <span className="swatch dash" /> Calendar event
          </li>
          {overlay.aid_status === "present" ? (
            <li>
              <span className="swatch bar" /> Lowy Institute aid (spent)
            </li>
          ) : null}
          {overlay.sentiment_status === "present" ? (
            <>
              <li>
                <span className="swatch tone" /> News tone, Global Database of Events, Language, and Tone (at least 5 articles)
              </li>
              <li>
                <span className="swatch polarity" /> Global Knowledge Graph items (darker is more negative, lighter is more positive)
              </li>
            </>
          ) : null}
        </>
      ) : null}
    </ul>
  );
}
