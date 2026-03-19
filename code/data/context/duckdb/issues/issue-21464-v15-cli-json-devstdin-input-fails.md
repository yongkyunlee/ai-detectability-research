# v1.5 CLI JSON `/dev/stdin` input fails

**Issue #21464** | State: closed | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** jgrg
**Labels:** needs triage

### What happens?

The new v1.5.0 CLI fails to read JSON on STDIN.

The v1.5.0 CLI is also missing the `-jsonlines` command line switch which is present in v1.4.4 to get ND-JSON / JSON Lines output.

### To Reproduce

The CLI of DuckDB v1.5.0 fails to handle JSON data on STDIN:
```sh
echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb -c "FROM read_json('/dev/stdin')"
┌────────┐
│  json  │
│  json  │
└────────┘
  0 rows
```

It works on v1.4.4:
```sh
echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb-1.4.4 -c "FROM read_json('/dev/stdin')"
┌─────────┬─────────┐
│ data_id │  study  │
│  int64  │ varchar │
├─────────┼─────────┤
│       1 │ one     │
│       2 │ two     │
└─────────┴─────────┘
```

The following, however, also fails on v1.4.4 with an error message:
```sh
echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb-1.4.4 -c "COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT JSON)"
Binder Error:
Positional reference 2 out of range (total 1 columns)
```

On v1.5.0 it doesn't produce any output or error.

### OS:

MacOS

### DuckDB Version:

1.5.0

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

Yes

## Comments

**carlopi:**
This looks to be a duplicate of https://github.com/duckdb/duckdb/issues/21278, and @Mytherin commented this is fixed via https://github.com/duckdb/duckdb/pull/21288 and a workaround would be adding `| cat`, see the comment at https://github.com/duckdb/duckdb/issues/21278#issuecomment-4048030556

You could also try a nightly duckdb version (see https://duckdb.org/install/preview), the `v1.5-` are expected to be working.

**jgrg:**
Yes, thanks, I just realised this.

I'll raise a separate issue for the missing `-jsonlines` switch and `COPY (...) TO '/dev/stdout' (FORMAT JSON)` not working.

**carlopi:**
`-jsonlines` I have also seen raised (and fixed), let me dig the PR. It was https://github.com/duckdb/duckdb/pull/21263 (reported at https://github.com/duckdb/duckdb/issues/21258)

**carlopi:**
And I just tested with a nightly binary, I think also `duckdb -c "COPY (SELECT 32) TO '/dev/stdout' (FORMAT JSON);"` now works (I guess a combination of the two above).

Thanks for raising those obviously!

We are getting ready for v1.5.1 that will have these fixed.

**jgrg:**
Ah, it is STDIN to STDOUT which fails:
```sh
echo '{"data_id":1,"study":"one"}\n{"data_id":2,"study":"two"}' | duckdb -c "COPY (FROM read_json('/dev/stdin')) TO '/dev/stdout' (FORMAT json)"
```
