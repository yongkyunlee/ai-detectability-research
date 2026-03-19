# LogicalTypeId::VARIANT not supported through ADBC

**Issue #21471** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** CurtHagenlocher
**Labels:** needs triage

### What happens?

When using ADBC to query a VARIANT column, the operation fails because the arrow_converter and arrow_appender don't support LogicalTypeId::VARIANT. If LogicalTypeId::VARIANT is always expected to be equivalent to a Parquet VARIANT then this is a fairly simple change as it's basically just a STRUCT plus metadata and I could submit a PR. Otherwise, feel free to close and I'll open this as a suggestion in Discussions instead.

### To Reproduce

Create a connection via ADBC and run e.g. the queries
```
INSERT INTO events VALUES (1, 42::VARIANT), (2, 'hello world'::VARIANT), (3, [1, 2, 3]::VARIANT), (4, {'name':'Alice'}::VARIANT);
SELECT * from events;
```

### OS:

Windows x86_64

### DuckDB Version:

1.5

### DuckDB Client:

ADBC

### Hardware:

_No response_

### Full Name:

Curt Hagenlocher

### Affiliation:

Apache Arrow

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)
