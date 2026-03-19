# CLI fails to `.open` a Parquet file

**Issue #21259** | State: closed | Created: 2026-03-10 | Updated: 2026-03-11
**Author:** Kretikus
**Labels:** reproduced

### What happens?

It looks like a dependency is missing:

The previous container versions (1.4.4) did support parquet files

### To Reproduce

Steps to reproduce:

Run the duckdb latest image and try to open a parquet file

### OS:

linux

### DuckDB Version:

1.5.0

### DuckDB Client:

duckdb

### Hardware:

_No response_

### Full Name:

Roman Himmes

### Affiliation:

INFORM Software

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**hannes:**
Thanks for reporting! The issue is not that the extension is not there, its that the `.open` / `attach` wiring does not work. If you query the file, e.g. `FROM '/opt/.../file.parquet'` it should work fine.

**hannes:**
And indeed this used to work with 1.4.4

**hannes:**
Fixed in https://github.com/duckdb/duckdb/pull/21269
