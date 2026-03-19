# Hive partition filters discover all files before pruning in 1.5.0

**Issue #21347** | State: open | Created: 2026-03-12 | Updated: 2026-03-18
**Author:** tlinhart
**Labels:** under review

### What happens?

When reading hive-partitioned Parquet files from S3 with filters on the partition columns, DuckDB 1.5.0 appears to discover all files matching the glob pattern first and then applies the hive partition filter afterward. In 1.4.4, it seems like only the matching files were ever touched.

I have ~120 hive-partitioned Parquet files on S3 at paths like:

```
s3://my-bucket/data/year=YYYY/month=M/data.parquet
```

When I query with a date range filter that should match only ~40 of
these files, the `EXPLAIN ANALYZE` output shows:

- v1.4.4: `Scanning Files: 39/39` – only matching files discovered
- v1.5.0: `Scanning Files: 39/122` – all 122 files discovered, then pruned to 39

The v1.5.0 behavior results in extra HTTP GET requests (presumably for reading Parquet footers of files that end up being filtered out), which adds noticeable latency when the files are on S3. I think this might be related to the new hierarchical S3 glob expansion introduced in 1.5.0.

### To Reproduce

Create a set of hive-partitioned Parquet files on S3 spanning many months (e.g. 10+ years of monthly data), then query with a filter that only needs a subset:

```sql
SELECT *
FROM read_parquet('s3://my-bucket/data/*/*/data.parquet')
WHERE
    last_day(make_date(year, month, 1)) >= DATE '2023-01-01' AND
    make_date(year, month, 1) <= DATE '2026-12-31';
```

Compare `EXPLAIN ANALYZE` output between v1.4.4 and v1.5.0, specifically the `Scanning Files: X/Y` line and the HTTPFS HTTP Stats (GET count).

### OS:

Linux (Ubuntu 24.04.4 LTS), x86_64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967a

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Tomáš Linhart

### Affiliation:

–

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for the report! We've managed to reproduce the regression - we will investigate.

**Mytherin:**
As a work-around you can use `SET s3_allow_recursive_globbing = false;` to restore the old behavior for now.

**cboettig:**
@Mytherin thanks for the work-around, the lack of dynamic partition pruning is really biting us too!  Would be fantastic to have faster globs but still be able to leverage pruning.  Greatly appreciate all you do for the community.

**Mytherin:**
Dynamic partition pruning [has been part of the system for a while](https://github.com/duckdb/duckdb/pull/12955). Maybe there is a specific query that is not triggering it that you could share?

**cboettig:**
@Mytherin apologies for being unclear, still wrapping my head around what we're seeing with S3 parquet files vs local parquet files.

It appears that we do not get _file level_ DPP pruning on a hive partitioned parquet on S3, it seems to be reading the parquet footers of every partition.  (we store the hive-level partition as a column in the individual parquet files as well).  I can send an example if that's helpful?

**Mytherin:**
We support full file pruning on dynamic filters, so yes an example would be helpful.

**cboettig:**
Thanks @Mytherin ! Ok I've tried to jot down my example and what I think is going on here,
let me know if this reproduces for you and if my take makes sense.

Dynamic Partition Pruning (DPP) fires during join execution but only prunes at
row-group level on S3, opening every partition file for a footer read. When the
partition key is encoded in the directory path, all matching/non-matching files can
be identified from path strings alone, with zero HTTP requests.

Adding a static `WHERE probe.h0 = X` literal to the probe side is **15x faster** because
it prunes at planning time. I think a DPP from the join should be able to produce the same result.

### reproducible code (I hope)

DuckDB 1.5.0. Reproduced against public S3-compatible storage (Ceph/NRP Nautilus,
`s3-west.nrp-nautilus.io`).

```python
import duckdb

con = duckdb.connect()
con.sql("""
SET THREADS=2;
INSTALL httpfs; LOAD httpfs;
SET s3_allow_recursive_globbing=false;
CREATE SECRET s3 (
    TYPE S3,
    ENDPOINT 's3-west.nrp-nautilus.io',
    URL_STYLE 'path',
    USE_SSL 'true',
    KEY_ID '', SECRET ''
);
""")

# Hive-partitioned datasets: s3://bucket/hex/h0={ubigint}/data_0.parquet
# carbon-2024: 94 h0 partitions, ~9.9 GiB total
# PADUS:       21 h0 partitions, ~7 GiB total
# H0 is a single partition cell covering part of California

CARBON = "s3://public-carbon/vulnerable-carbon-2024/hex/**"
PADUS  = "s3://public-padus/padus-4-1/fee/hex/**"
H0     = 577199624117288959

# Query A: join-derived DPP
# Build side (parks) filters to h0=H0. DPP should prune carbon to 1/94 files.
# Actual: all 94 carbon files opened for footer reads.
query_a = f"""
    WITH parks AS (
        SELECT DISTINCT h8
        FROM read_parquet('{PADUS}')
        WHERE State_Nm = 'CA' AND Des_Tp = 'NP'
          AND h0 = {H0}
    )
    SELECT SUM(c.carbon)/1e6
    FROM parks p
    JOIN read_parquet('{CARBON}') c ON p.h8 = c.h8
"""

# Query B: static WHERE on probe side (workaround)
# Identical logic; adding WHERE c.h0 = H0 enables file-level pruning at plan time.
query_b = query_a.rstrip() + f"\n    WHERE c.h0 = {H0}\n"

for label, q in [("A_join_dpp", query_a), ("B_static_literal", query_b)]:
    rows = con.sql(f"EXPLAIN ANALYZE {q}").fetchall()
    text = "\n".join(r[1] for r in rows)
    print(f"\n--- {label} ---")
    for line in text.split("\n"):
        if any(x in line for x in ["Files Read", "GET", " in:", "Dynamic", "Total Time"]):
            print(" ", line.strip())
```

### What I see: 

```
--- A_join_dpp ---
  Dynamic Filters: (present — DPP is active)
  Total Files Read: 94
  #GET: 6717
  in: 1.3 GiB
  Total Time: 407s

--- B_static_literal ---
  Total Files Read: 1
  #GET: 546
  in: 109 MiB
  Total Time: 27s
```

**15x fewer files, 12x less data, 15x faster** — from adding one `WHERE c.h0 = {H0}`.
The join in Query A produces an identical result; DPP is shown as active but does not
prune at file level.

## Notes

The hive partition key `h0` appears both inside each file (as a column, enabling
row-group statistics) and in the directory path (`hex/h0=577199624117288959/data_0.parquet`).

DuckDB uses the in-file column for DPP, which requires a footer read from every file
to check row-group statistics. It does not use the path encoding to prune the file list.

For **local files**, DuckDB 1.5.0 added file-level DPP (PR #19888): the file list can
be filtered after the build side materializes. 

For **S3**, the file list is enumerated via `LIST` requests at planning time and is
locked in before execution. 

## Potential fix?

After materializing the build side and computing DPP filter values, match those values
against hive partition directory names in the pre-enumerated path list — before issuing
any HTTP requests for parquet footers. I think the path list is already available from planning
time so this should require zero additional S3 requests.

## Related

- PR #19888 — file-level DPP for local filesystem (1.5.0)
- Issue #17352 — original DPP tracking issue for hive partition joins
- Issue #21347 — `s3_allow_recursive_globbing` regression (separate, 1.5.0)

**Mytherin:**
That doesn't really seem equivalent, no? The join is on `h8`, not on `h0`. Maybe you meant to include `c.h0 = p.h0` in the join condition?

**Mytherin:**
Query plans and files read look identical to me if I include that as a join condition:

```sql
    WITH parks AS (
        SELECT DISTINCT h0, h8
        FROM read_parquet('{PADUS}')
        WHERE State_Nm = 'CA' AND Des_Tp = 'NP'
          AND h0 = {H0}
    )
    SELECT SUM(c.carbon)/1e6
    FROM parks p
    JOIN read_parquet('{CARBON}') c ON p.h8 = c.h8 AND p.h0 = c.h0
```

(Note that the second query still executes much faster due to the HTTP cache, of course).

**cboettig:**
Argh indeed!  thought I'd fixed that.  yup, when I actually include `c.h0 = p.h0` it works as expected.  my apologies for the noise!
