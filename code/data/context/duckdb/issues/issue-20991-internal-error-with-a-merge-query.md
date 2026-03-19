# Internal ERROR with a MERGE query

**Issue #20991** | State: closed | Created: 2026-02-17 | Updated: 2026-03-12
**Author:** mat813
**Labels:** reproduced, Breaking Change

### What happens?

```
INTERNAL Error:
Failed to bind column reference "id" [17.0] (bindings: {#[16.0], #[16.1], #[16.2], #[16.3], #[30.0], #[30.1], #[30.2], #[30.3], #[30.4], #[30.5], #[30.6], #[30.7], #[30.8]})

Stack Trace:

duckdb() [0xa29206]
duckdb() [0xa292c4]
duckdb() [0xa2e621]
duckdb() [0xc23034]
duckdb() [0x4a2dbd]
duckdb() [0xfddd0b]
duckdb() [0xfde521]
duckdb() [0xfdf415]
duckdb() [0xfde55c]
duckdb() [0xfdf415]
duckdb() [0xfdf69e]
duckdb() [0xfdfd25]
duckdb() [0xfeb85d]
duckdb() [0xc0b77b]
duckdb() [0xfeb85d]
duckdb() [0xc0b77b]
duckdb() [0xfeb85d]
duckdb() [0xc0b77b]
duckdb() [0xfeb85d]
duckdb() [0xc0b77b]
duckdb() [0xc0c07b]
duckdb() [0xc0c23a]
duckdb() [0xcae9fa]
duckdb() [0xcaf4b4]
duckdb() [0xcbf1fc]
duckdb() [0xcc9497]
duckdb() [0xcc96af]
duckdb() [0xcca5d9]
duckdb() [0xccbe6f]
duckdb() [0xccbf63]
duckdb() [0xccd56e]
duckdb() [0x83044d]
duckdb() [0x811630]
duckdb() [0x8122cb]
duckdb() [0x812943]
duckdb() [0x803f1b]
/lib/x86_64-linux-gnu/libc.so.6(+0x29d90) [0x78699be29d90]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x80) [0x78699be29e40]
duckdb() [0x80839e]

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### To Reproduce

```sql
create schema raw;
create schema hist;
create schema silver;
CREATE TABLE hist.ingestion_watermark("source" VARCHAR, entity VARCHAR, last_collected_at TIMESTAMP, PRIMARY KEY("source", entity));
CREATE TABLE raw.ovirt_mac_pool_dedup(id UUID, collected_at TIMESTAMP WITH TIME ZONE, "name" VARCHAR, description VARCHAR, ranges VARCHAR, allow_duplicates BOOLEAN, default_pool BOOLEAN, sig VARCHAR);
CREATE TABLE raw.ovirt_mac_pool_norm(id UUID, collected_at TIMESTAMP WITH TIME ZONE, "name" VARCHAR, description VARCHAR, ranges VARCHAR, allow_duplicates BOOLEAN, default_pool BOOLEAN, sig VARCHAR);

BEGIN TRANSACTION;

CREATE SCHEMA IF NOT EXISTS silver;
CREATE TABLE IF NOT EXISTS silver.ovirt_mac_pool_hist (
      id UUID,
      name VARCHAR,
      description VARCHAR,
      ranges VARCHAR,
      allow_duplicates BOOLEAN,
      default_pool BOOLEAN,
      sig VARCHAR,
      _valid_from TIMESTAMP WITH TIME ZONE,
      _valid_until TIMESTAMP WITH TIME ZONE,
      _is_current BOOLEAN
  );

WITH src AS (
      SELECT
        *
      FROM
        raw.ovirt_mac_pool_dedup
  ),
  run AS (
    SELECT max(collected_at) AS run_ts FROM src
  )
  MERGE INTO silver.ovirt_mac_pool_hist AS target
  USING src AS source
  ON (target.id = source.id AND target._is_current = true)
  
  WHEN MATCHED AND (target.sig <> source.sig) THEN
    UPDATE SET
      _valid_until = source.collected_at,
      _is_current = false
  
  WHEN NOT MATCHED BY SOURCE AND target._is_current = true THEN
    UPDATE SET
      _valid_until = (SELECT run_ts FROM run),
      _is_current = false
  
  WHEN NOT MATCHED BY TARGET THEN
    INSERT (
        id,
        name,
        description,
        ranges,
        allow_duplicates,
        default_pool,
        sig,
        _valid_from,
        _valid_until,
        _is_current
      )
    VALUES
      (
        source.id,
        source.name,
        source.description,
        source.ranges,
        source.allow_duplicates,
        source.default_pool,
        source.sig,
        source.collected_at,
        null,
        true
      );
COMMIT;
```

### OS:

Ubuntu Linux, 6.8.0-94-generic x86_64 GNU/Linux

### DuckDB Version:

v1.4.4 (Andium) 6ddac802ff

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

Mathieu Arnold

### Affiliation:

OVEA

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**hannes:**
Thanks, I could reproduce this issue.
