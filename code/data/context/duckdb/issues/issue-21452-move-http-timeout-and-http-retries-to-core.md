# Move `http_timeout` and `http_retries` to core

**Issue #21452** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** carlopi
**Labels:** under review

### What happens?

This is a follow up of https://github.com/duckdb/duckdb/issues/20797, tracking it here so original reporters could follow eventual progress / decisions on the matter.

Currently extension [auto-]installation (if `httpfs` is not available locally) are done via httplib-based HTTPUtil.

I would propose revisiting (for next minor release) lifting some http-settings from `duckdb-httpfs` to core, so that they can be already used in extension installations or used by other network extensions.

See conversation at https://github.com/duckdb/duckdb/issues/20797

### To Reproduce

See https://github.com/duckdb/duckdb/issues/20797 for setup

### OS:

any

### DuckDB Version:

v1.5.0

### DuckDB Client:

any

### Hardware:

_No response_

### Full Name:

Carlo Piovesan

### Affiliation:

DuckDB Labs

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set
