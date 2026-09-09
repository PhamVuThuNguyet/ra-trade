"use client";

import type { DataTypeId, SourceId } from "../lib/catalog";

type Props = {
  sourceId: SourceId;
  dataTypeId: DataTypeId;
  sources: { id: SourceId; display_name: string }[];
  dataTypes: { id: DataTypeId; display_name: string }[];
  onSource: (id: SourceId) => void;
  onDataType: (id: DataTypeId) => void;
  viewMode: "table" | "plot";
  onViewMode: (mode: "table" | "plot") => void;
};

export function SourceTypeControls({
  sourceId,
  dataTypeId,
  sources,
  dataTypes,
  onSource,
  onDataType,
  viewMode,
  onViewMode,
}: Props) {
  return (
    <section className="panel" aria-label="Source and view">
      <label>
        Source
        <select value={sourceId} onChange={(event) => onSource(event.target.value as SourceId)}>
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.display_name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Data type
        <select
          value={dataTypeId}
          onChange={(event) => onDataType(event.target.value as DataTypeId)}
        >
          {dataTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.display_name}
            </option>
          ))}
        </select>
      </label>
      <fieldset className="view-toggle">
        <legend>View</legend>
        <div className="view-choices">
          <label>
            <input
              type="radio"
              name="view"
              checked={viewMode === "table"}
              onChange={() => onViewMode("table")}
            />
            Table
          </label>
          <label>
            <input
              type="radio"
              name="view"
              checked={viewMode === "plot"}
              onChange={() => onViewMode("plot")}
            />
            Plot
          </label>
        </div>
      </fieldset>
    </section>
  );
}
