# VACUUM FULL not implemented — no native way to reclaim space after deletes/drops

**Issue #21154** | State: open | Created: 2026-03-03 | Updated: 2026-03-03
**Author:** andreamoro

## Summary

DuckDB has no native mechanism to reclaim disk space after deletes, table drops, or heavy batch-insert/replace workloads. `VACUUM`, `VACUUM ANALYZE`, and `CHECKPOINT` are all no-ops for space reclamation. `VACUUM FULL` raises `Not implemented Error`. This is a recurring operational pain point with no first-class solution.

## Reproduction / Evidence

**Workload:** A processing pipeline writing output to a single `.duckdb` file over multiple runs, involving repeated `INSERT OR REPLACE` and `DELETE` operations across several tables.

**Observed file size:** 1.26 GB

**`pragma_database_size()` output:**

| metric | value |
|---|---|
| `block_size` | 262144 |
| `free_blocks` | 1,354 |
| `total_blocks` | 5,169 |
| **dead space** | **~26% of file** |

Commands attempted — all either no-ops or errors:

```sql
VACUUM;
VACUUM ANALYZE;
CHECKPOINT;
VACUUM FULL;  -- Not implemented Error
```

## Workaround

The only working solution currently is a manual database copy via an in-memory connection:

```python
with duckdb.connect(":memory:") as conn:
    conn.execute(f"ATTACH '{source_path}' AS source (READ_ONLY)")
    conn.execute(f"ATTACH '{compact_path}' AS target")
    conn.execute("COPY FROM DATABASE source TO target")
```

**Result: 1.26 GB → 256 MB (80% reduction, 1.01 GB reclaimed) in under 5 seconds.**

This does work, though having a native `VACUUM` option would remove the necessity to support custom-made solutions like this, which can be brittle over time and require extra operational steps: a maintenance window, enough free disk space to hold a full second copy simultaneously, and manual file management (rename, delete).

## Related Issues

This issue has been reported in various forms over several years:

- #109 — original VACUUM feature request (2019)
- #12286 — file size large after deleting data / dropping tables
- #14124 — DROP TABLE does not reduce database size
- #17778 — `.duckdb` file size growing (ART index root cause identified)
- #19468 — UNIQUE/PK constraint causes unbounded growth (confirmed bug, @Mytherin)

The consistent thread across all of these: **users have no way to ask DuckDB to compact its own file**.

## Request

It would be wonderful to see `VACUUM FULL` (or an equivalent `COMPACT` / `REPACK` command) implemented — one that performs an in-place or atomic database compaction without requiring the user to manage a second copy of the database manually.

The `COPY FROM DATABASE` workaround demonstrates the underlying capability already exists — it just needs to be surfaced as a first-class operation. An ideal implementation would:

1. Work in-process (no external tooling required)
2. Not require a full second copy of the database on disk simultaneously (e.g. compact block-by-block, or use a temp file with atomic rename — much as we do in the workaround above)
3. Be safe to run on a live database, or clearly document that exclusive access is required

DuckDB is increasingly used in production pipelines where databases grow and shrink over time. Without native space reclamation, operators are left maintaining custom scripts or accepting unbounded file growth. A native solution would be a meaningful quality-of-life improvement for a large number of users.
