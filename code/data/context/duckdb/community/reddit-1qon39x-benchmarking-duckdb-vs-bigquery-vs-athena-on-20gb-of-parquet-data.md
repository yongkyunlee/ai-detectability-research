# Benchmarking DuckDB vs BigQuery vs Athena on 20GB of Parquet data

**r/dataengineering** | Score: 23 | Comments: 20 | Date: 2026-01-27
**Author:** explorer_soul99
**URL:** https://www.reddit.com/r/dataengineering/comments/1qon39x/benchmarking_duckdb_vs_bigquery_vs_athena_on_20gb/

I'm building an integrated data + compute platform and couldn't find good apples-to-apples comparisons online. So I ran some benchmarks and wanted to share. Sharing here to gather feedback.

Test dataset is ~20GB of financial time-series data in Parquet (ZSTD compressed), 57 queries total.

---

## TL;DR

Platform | Warm Median | Cost/Query | Data Scanned
:--|:--|:--|:--
DuckDB Local (M) | 881 ms | - | -
DuckDB Local (XL) | 284 ms | - | -
DuckDB + R2 (M) | 1,099 ms | - | -
DuckDB + R2 (XL) | 496 ms | - | -
BigQuery | 2,775 ms | $0.0282 | 1,140 GB
Athena | 4,211 ms | $0.0064 | 277 GB

*M = 8 threads, 16GB RAM | XL = 32 threads, 64GB RAM*

**Key takeaways:**

1. DuckDB on local storage is 3-10x faster than cloud platforms
2. BigQuery scans 4x more data than Athena for the same queries
3. DuckDB + remote storage has significant cold start overhead (14-20 seconds)

---

## The Setup

**Hardware (DuckDB tests):**

- CPU: AMD EPYC 9224 24-Core (48 threads)
- RAM: 256GB DDR
- Disk: Samsung 870 EVO 1TB (SATA SSD)
- Network: 1 Gbps
- Location: Lauterbourg, FR

**Platforms tested:**

Platform | Configuration | Storage
:--|:--|:--
DuckDB (local) | 1-32 threads, 2-64GB RAM | Local SSD
DuckDB + R2 | 1-32 threads, 2-64GB RAM | Cloudflare R2
BigQuery | On-demand serverless | Google Cloud
Athena | On-demand serverless | S3 Parquet

**DuckDB configs:**

    Minimal:  1 thread,  2GB RAM,   5GB temp (disk spill)
    Small:    4 threads, 8GB RAM,  10GB temp (disk spill)
    Medium:   8 threads, 16GB RAM, 20GB temp (disk spill)
    Large:   16 threads, 32GB RAM, 50GB temp (disk spill)
    XL:      32 threads, 64GB RAM, 100GB temp (disk spill)

**Methodology:**

- 57 queries total: 42 typical analytics (scans, aggregations, joins, windows) + 15 wide scans
- 4 runs per query: First run = cold, remaining 3 = warm
- All platforms queried identical Parquet files
- Cloud platforms: On-demand pricing, no reserved capacity

---

## Why Is DuckDB So Fast?

DuckDB's vectorized execution engine processes data in batches, making efficient use of CPU caches. Combined with local SSD storage (no network latency), it consistently delivered sub-second query times.

Even with medium config (8 threads, 16GB), DuckDB Local hit 881ms median. With XL (32 threads, 64GB), that dropped to 284ms.

For comparison:

- BigQuery: 2,775ms median (3-10x slower)
- Athena: 4,211ms median (~5-15x slower)

---

## DuckDB Scaling

Config | Threads | RAM | Wide Scan Median
:--|:--|:--|:--
Small | 4 | 8GB | 4,971 ms
Medium | 8 | 16GB | 2,588 ms
Large | 16 | 32GB | 1,446 ms
XL | 32 | 64GB | 995 ms

Doubling resources roughly halves latency. Going from 4 to 32 threads (8x) improved performance by 5x. Not perfectly linear but predictable enough for capacity planning.

---

## Why Does Athena Scan Less Data?

Both charge $5/TB scanned, but:

- BigQuery scanned 1,140 GB total
- Athena scanned 277 GB total

That's a 4x difference for the same queries.

Athena reads Parquet files directly and uses:

- **Column pruning:** Only reads columns referenced in the query
- **Predicate pushdown:** Applies WHERE filters at the storage layer
- **Row group statistics:** Uses min/max values to skip entire row groups

BigQuery reports higher bytes scanned, likely due to how external tables are processed (BigQuery rounds up to 10MB minimum per table scanned).

---

## Performance by Query Type

Category | DuckDB Local (XL) | DuckDB + R2 (XL) | BigQuery | Athena
:--|:--|:--|:--|:--
Table Scan | 208 ms | 407 ms | 2,759 ms | 3,062 ms
Aggregation | 382 ms | 411 ms | 2,182 ms | 2,523 ms
Window Functions | 947 ms | 12,187 ms | 3,013 ms | 5,389 ms
Joins | 361 ms | 892 ms | 2,784 ms | 3,093 ms
Wide Scans | 995 ms | 1,850 ms | 3,588 ms | 6,006 ms

Observations:

- DuckDB Local is 5-10x faster across most categories
- Window functions hurt DuckDB + R2 badly (requires multiple passes over remote data)
- Wide scans (SELECT *) are slow everywhere, but DuckDB still leads

---

## Cold Start Analysis

This is often overlooked but can dominate user experience for sporadic workloads.

Platform | Cold Start | Warm | Overhead
:--|:--|:--|:--
DuckDB Local (M) | 929 ms | 881 ms | ~5%
DuckDB Local (XL) | 307 ms | 284 ms | ~8%
DuckDB + R2 (M) | 19.5 sec | 1,099 ms | ~1,679%
DuckDB + R2 (XL) | 14.3 sec | 496 ms | ~2,778%
BigQuery | 2,834 ms | 2,769 ms | ~2%
Athena | 3,068 ms | 3,087 ms | ~0%

DuckDB + R2 cold starts range from 14-20 seconds. First query fetches Parquet metadata (file footers, schema, row group info) over the network. Subsequent queries are fast because metadata is cached.

DuckDB Local has minimal overhead (~5-8%). BigQuery and Athena also minimal (~2% and ~0%).

---

## Wide Scans Change Everything

Added 15 SELECT * queries to simulate data exports, ML feature extraction, backup pipelines.

Platform | Narrow Queries (42) | With Wide Scans (57) | Change
:--|:--|:--|:--
Athena | $0.0037/query | $0.0064/query | +73%
BigQuery | $0.0284/query | $0.0282/query | -1%

Athena's cost advantage comes from column pruning. When you SELECT *, there's nothing to prune. Costs converge toward BigQuery's level.

---

## Storage Costs (Often Overlooked)

Query costs get attention, but storage is recurring:

Provider | Storage ($/GB/mo) | Egress ($/GB)
:--|:--|:--
AWS S3 | $0.023 | $0.09
Google GCS | $0.020 | $0.12
Cloudflare R2 | $0.015 | $0.00

R2 is 35% cheaper than S3 for storage. Plus zero egress fees.

**Egress math for DuckDB + remote storage:**

1000 queries/day × 5GB each:

- S3: $0.09 × 5000 = $450/day = **$13,500/month**
- R2: **$0/month**

That's not a typo. Cloudflare doesn't charge egress on R2.

---

## When I'd Use Each

Scenario | My Pick | Why
:--|:--|:--
Sub-second latency required | DuckDB local | 5-8x faster than cloud
Large datasets, warm queries OK | DuckDB + R2 | Free egress
GCP ecosystem | BigQuery | Integration convenience
Sporadic cold queries | BigQuery | Minimal cold start penalty

---

## Data Format

- **Compression:** ZSTD
- **Partitioning:** None
- **Sort order:** (symbol, dateEpoch) for time-series tables
- **Total:** 161 Parquet files, ~20GB

Table | Files | Size
:--|:--|:--
stock_eod | 78 | 12.2 GB
financial_ratios | 47 | 3.6 GB
income_statement | 19 | 1.6 GB
balance_sheet | 15 | 1.8 GB
profile | 1 | 50 MB
sp500_constituent | 1 | &lt;1 MB

---

## Data and Compute Locations

Platform | Data Location | Compute Location | Co-located?
:--|:--|:--|:--
BigQuery | europe-west1 (Belgium) | europe-west1 | Yes
Athena | S3 eu-west-1 (Ireland) | eu-west-1 | Yes
DuckDB + R2 | Cloudflare R2 (EU) | Lauterbourg, FR | Network hop
DuckDB Local | Local SSD | Lauterbourg, FR | Yes

BigQuery and Athena co-locate data and compute. DuckDB + R2 has a network hop explaining the cold start penalty. Local DuckDB eliminates network entirely.

---

## Limitations

- **No partitioning:** Test data wasn't partitioned. Partitioning would likely improve all platforms.
- **Single region:** European regions only. Results may vary elsewhere.
- **ZSTD compression:** Other codecs (Snappy, LZ4) may show different results.
- **No caching:** No Redis/Memcached.

---

## Raw Data

Full benchmark code and result CSVs: [GitHub - Insydia-Studio/benchmark-duckdb-athena-bigquery](https://github.com/Insydia-Studio/benchmark-duckdb-athena-bigquery)

**Result files:**

- duckdb_local_benchmark - 672 query runs
- duckdb_r2_benchmark - 672 query runs
- cloud_benchmark (BigQuery) - 168 runs
- athena_benchmark - 168 runs
- wide_scan_* files - 510 runs total

---

Happy to answer questions about specific query patterns or methodology. Also curious if anyone has run similar benchmarks with different results.
