"use client";

type Props = {
  columns: string[];
  rows: Record<string, unknown>[];
  indexLabels?: Record<string, string>;
};

export function DataTable({ columns, rows, indexLabels }: Props) {
  if (rows.length === 0) {
    return null;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{formatCell(row[column], column, indexLabels)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(
  value: unknown,
  column: string,
  indexLabels?: Record<string, string>,
): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (column === "index_id" && indexLabels && indexLabels[String(value)]) {
    return indexLabels[String(value)];
  }
  return String(value);
}
