"use client";

import type { ProductGroupId } from "../lib/catalog";

type Props = {
  reporters: string[];
  selectedReporter: string;
  onReporter: (value: string) => void;
  yearMin: string;
  yearMax: string;
  onYearMin: (value: string) => void;
  onYearMax: (value: string) => void;
  productGroupId: ProductGroupId;
  productGroups: { id: ProductGroupId; display_name: string }[];
  onProductGroup: (id: ProductGroupId) => void;
};

export function FilterBar({
  reporters,
  selectedReporter,
  onReporter,
  yearMin,
  yearMax,
  onYearMin,
  onYearMax,
  productGroupId,
  productGroups,
  onProductGroup,
}: Props) {
  return (
    <section className="panel" aria-label="Filters">
      <label>
        Reporter (PIC)
        <select value={selectedReporter} onChange={(event) => onReporter(event.target.value)}>
          <option value="">All reporters</option>
          {reporters.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Year from
        <input value={yearMin} onChange={(event) => onYearMin(event.target.value)} inputMode="numeric" />
      </label>
      <label>
        Year to
        <input value={yearMax} onChange={(event) => onYearMax(event.target.value)} inputMode="numeric" />
      </label>
      <label>
        Product group
        <select
          value={productGroupId}
          onChange={(event) => onProductGroup(event.target.value as ProductGroupId)}
        >
          {productGroups.map((group) => (
            <option key={group.id} value={group.id}>
              {group.display_name}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}
