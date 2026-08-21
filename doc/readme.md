# Kards Data Engineering Pipeline — Version 2 (Low-Code)

The low-code counterpart to
[KARDS-Data-Engineering-Code-Heavy-1](https://github.com/LS1SHOGUN/KARDS-Data-Engineering-Code-Heavy-1)
— the same medallion architecture (Bronze → Silver → Gold → Power BI), built on
the same source data, using Microsoft Fabric's visual/low-code tools instead of
Python and PySpark.

Full comparison of both approaches:
[Version_Comparison.md](https://github.com/LS1SHOGUN/KARDS-Data-Engineering-Code-Heavy-1/blob/main/docs/Version_Comparison.md)

## What this version does

Pulls the same card and card-relationship data from a local SQL Server database,
using entirely Fabric-native tools — no local scripts, no Python, no manual
export/upload step. Unlike Version 1, the entire pipeline (ingestion through
Gold) runs as a **single orchestrated Data Factory pipeline**, rather than
separately-triggered items.

## Architecture

```
Local SQL Server
   │
   ▼  (single Data Factory pipeline, one run end to end)
   ┌────────────────────────────────────────────────────────┐
   │  1. Copy Data (via On-premises Data Gateway)            │
   │     → lands raw table data in Bronze                    │
   │                                                          │
   │  2. Dataflow Gen2 activity — Files → Silver              │
   │     → Power Query column-pruning                         │
   │                                                          │
   │  3. Dataflow Gen2 activity — Silver → Gold                │
   │     → Power Query Merge Queries + Filter Rows             │
   └────────────────────────────────────────────────────────┘
   │
   ▼
KardsLakehouseV2 (Bronze/Silver/Gold)
   │
   ▼
Power BI (semantic model on Gold)
```

Built in a fully separate Lakehouse (`KardsLakehouseV2`) from Version 1, so both
implementations can be compared side by side without interfering with each other.

## Components

- **Data Factory pipeline** — the single orchestrating pipeline. Starts with a
  Copy Data activity (connected to the local SQL Server via the On-premises
  Data Gateway) that lands raw table data into Bronze, then chains directly into
  the two Dataflow Gen2 activities below — all three stages trigger and run as
  one pipeline execution.
- **Dataflow Gen2 activity (Files → Silver)** — reads the Bronze Parquet files
  and applies the same column-pruning logic as Version 1's Silver layer
  (dropping image paths and audit timestamps), done visually with Power Query's
  Remove Columns.
- **Dataflow Gen2 activity (Silver → Gold)** — recreates the same Gold tables as
  Version 1 (`spawn_chain` via Merge Queries, `eligible_for_forecast`/
  `veteran_cards`/`permanent_pool_cards` via Filter Rows) with no code.
- **Power BI report** — connected to the Gold semantic model, same reporting
  approach as Version 1.

## Notable differences from Version 1

- **Ingestion**: Version 1's ingestion ran as a local Python script requiring
  Task Scheduler and manual credential management. Version 2's ingestion runs
  entirely inside Fabric, authenticated through the gateway — no dependency on a
  local machine being on.
- **Orchestration**: Version 1 kept Bronze, Silver, and Gold as independently
  triggered steps (a scheduled script, notebook cells run manually, a separate
  Warehouse refresh pipeline). Version 2 chains all three stages into a single
  pipeline, triggered and monitored as one end-to-end run — closer to how a
  production pipeline would actually be operated.
- **Setup cost**: getting the gateway connection working reliably (a transient
  cloud relay error, a Windows service-account permissions issue, and an
  encrypted-connection mismatch with the local SQL Server) was the most
  time-consuming part of this entire version — more so than any of the actual
  transformation or orchestration work.

## Notes

- No local script or credentials are involved in this version — all
  authentication is handled by the On-premises Data Gateway and Fabric's own
  connection management.
- This repo contains exported artifacts (pipeline/dataflow definitions) for
  reference; the pipeline and dataflows themselves run inside Fabric and are not
  independently executable outside that environment.
