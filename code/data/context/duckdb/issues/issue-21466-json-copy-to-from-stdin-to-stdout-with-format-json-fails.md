# JSON `COPY TO` from STDIN to STDOUT with `(FORMAT json)` fails

**Issue #21466** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** jgrg
**Labels:** reproduced

### What happens?

In both v1.4.4 and v1.5.0, and with both the CLI or API via Python or Rust, doing:

```sql
COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT json)
```

fails, whereas CSV output works:
```sql
COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT csv)
```

### To Reproduce

CSV output works:
```sh
$ echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb -c "COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT csv)" | cat
data_id,study
1,one
2,two
```

JSON output fails:
```sh
$ echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb -c "COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT json)" | cat
Binder Error:
Positional reference 2 out of range (total 1 columns)
```

### OS:

MacOS

### DuckDB Version:

1.4.4 1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

James Gilbert

### Affiliation:

Wellcome Sanger Institue

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)
