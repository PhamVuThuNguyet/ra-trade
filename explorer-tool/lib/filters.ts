export type TableRow = Record<string, unknown>;

export function filterRows(
  rows: TableRow[],
  options: {
    reporters?: string[];
    yearMin?: number | null;
    yearMax?: number | null;
  },
): TableRow[] {
  let selected = rows;
  if (options.reporters && options.reporters.length > 0) {
    const names = new Set(options.reporters);
    selected = selected.filter((row) => names.has(String(row.country ?? "")));
  }
  if (options.yearMin != null) {
    const minimum = options.yearMin;
    selected = selected.filter((row) => Number(row.year) >= minimum);
  }
  if (options.yearMax != null) {
    const maximum = options.yearMax;
    selected = selected.filter((row) => Number(row.year) <= maximum);
  }
  return selected;
}
