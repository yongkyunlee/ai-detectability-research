# Heredoc does not work with DuckDB CLI v1.5.0

**Issue #21245** | State: closed | Created: 2026-03-09 | Updated: 2026-03-09
**Author:** prmoore77
**Labels:** needs triage

### What happens?

I frequently use heredocs with DuckDB CLI - example script:
```bash
duckdb << EOF
SELECT version();
EOF
```

This has worked fine up through v1.4.4 - but when I installed v1.5.0 today - the SQL command no longer runs...

### To Reproduce

Just run this from a bash prompt:
```bash
duckdb << EOF
SELECT version();
EOF
```

### OS:

macOS

### DuckDB Version:

v1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Philip Moore

### Affiliation:

GizmoData

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**carlopi:**
Looks to be closely related to https://github.com/duckdb/duckdb/issues/21243 (duplicate?)

**carlopi:**
I think it will be fixed via https://github.com/duckdb/duckdb/pull/21247
