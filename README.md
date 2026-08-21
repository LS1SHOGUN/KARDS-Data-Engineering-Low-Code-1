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
export/upload step.

## Architecture

```
Local SQL Server
   → Data Factory Copy Data pipeline (via On-premises Data Gateway)
   → Bronze (KardsLakehouseV2, Files/Tables)
   → Silver (Dataflow Gen2 #1 — Files → Silver, Power Query)
   → Gold (Dataflow Gen2 #2 — Silver → Gold, Power Query Merge/Filter)
   → Power BI (semantic model on KardsLakehouseV2 Gold)
```

Built in a fully separate Lakehouse (`KardsLakehouseV2`) from Version 1, so both
implementations can be compared side by side without interfering with each other.

## Components

- **Data Factory pipeline** — a Lookup + Copy Data pipeline that connects to the
  local SQL Server via the On-premises Data Gateway (`local_gateway`) and lands
  raw table data into Bronze. No transformation logic — pure data movement.
- **Dataflow Gen2 (Files → Silver)** — reads the Bronze Parquet files and applies
  the same column-pruning logic as Version 1's Silver layer (dropping image paths
  and audit timestamps), done visually with Power Query's Remove Columns.
- **Dataflow Gen2 (Silver → Gold)** — recreates the same Gold tables as Version 1
  (`spawn_chain` via Merge Queries, `eligible_for_forecast`/`veteran_cards`/
  `permanent_pool_cards` via Filter Rows) with no code.
- **Power BI report** — connected to the Gold semantic model, same reporting
  approach as Version 1.

## Notable difference from Version 1

Version 1's ingestion ran as a local Python script requiring Task Scheduler and
manual credential management. Version 2's ingestion runs entirely inside Fabric,
authenticated through the gateway — no dependency on a local machine being on.
The tradeoff: getting the gateway connection working reliably (a transient cloud
relay error, a Windows service-account permissions issue, and an encrypted-
connection mismatch with the local SQL Server) was the most time-consuming part
of this entire version — more so than any of the actual transformation work.

## Notes

- No local script or credentials are involved in this version — all
  authentication is handled by the On-premises Data Gateway and Fabric's own
  connection management.
- This repo contains exported artifacts (pipeline/dataflow definitions) for
  reference; the pipeline and dataflows themselves run inside Fabric and are not
  independently executable outside that environment.
