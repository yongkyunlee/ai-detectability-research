# Reading stdin fails on macOS

**Issue #21278** | State: closed | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** maskati
**Labels:** reproduced

### What happens?

Reading stdin fails with 1.5.0 on macOS. 1.4.4 works on macOS. Both work on Linux.

### To Reproduce

Reproduce on macOS with `echo '{"foo":"bar"}' | duckdb -c "SELECT version();SELECT * FROM read_ndjson('/dev/stdin');"`.

With 1.4.4:
```
┌─────────────┐
│ "version"() │
│   varchar   │
├─────────────┤
│ v1.4.4      │
└─────────────┘
┌─────────┐
│   foo   │
│ varchar │
├─────────┤
│ bar     │
└─────────┘
```
With 1.5.0:
```
┌─────────────┐
│ "version"() │
│   varchar   │
├─────────────┤
│ v1.5.0      │
└─────────────┘
┌────────┐
│  json  │
│  json  │
└────────┘
```

### OS:

macOS

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Majid Maskati

### Affiliation:

Mallow

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**hannes:**
Thanks for filing this, I was able to reproduce this. We will have a look.

**hannes:**
This may be related to https://github.com/duckdb/duckdb/issues/21243

**Mytherin:**
Thanks for filing - this is indeed the same issue as https://github.com/duckdb/duckdb/issues/21243 but manifesting in a different form. This has been fixed in https://github.com/duckdb/duckdb/pull/21288 and a fix will be part of v1.5.1.

As a work-around you can pipe the output to `| cat`.

```
echo '{"foo":"bar"}' | duckdb -c "SELECT version();SELECT * FROM read_ndjson('/dev/stdin');" | cat 
┌─────────────┐
│ "version"() │
│   varchar   │
├─────────────┤
│ v1.5.0      │
└─────────────┘
┌─────────┐
│   foo   │
│ varchar │
├─────────┤
│ bar     │
└─────────┘
```
