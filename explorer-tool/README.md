# Explorer Tool

Researcher UI for PIC–partner influence tables and plots. Analysis pipelines stay in the Python analysis packages. This folder holds the Next.js app and the catalog builder (`explorer_catalog/`).

## Start

From this directory:

```text
npm install
npm run dev
```

Open the URL Next.js prints (usually `http://localhost:3000`). The catalog is `public/data/catalog.json`.

To refresh the catalog from study CSVs, at the repository root:

```text
python scripts/export_explorer_catalog.py
```

That command must not fetch Lowy or EM-DAT. Overlay layers that are missing are named in the plot view. Analysis packages must not import `explorer_catalog` or this folder.

## What you should see

- Table: BACI or Comtrade goods trade, or labelled mock Services. No partner picker; Australia, China, and the United States are always in the table.
- Plot: six index charts (I, E, CWI, CWE, CWI essential, CWE essential), three solid partner colours, calendar / Lowy aid / EM-DAT overlays when present.
