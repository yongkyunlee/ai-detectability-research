# DuckDB CLI no longer reads SQL statements from stdin in v1.5.0

**Issue #21253** | State: closed | Created: 2026-03-09 | Updated: 2026-03-10
**Author:** jake-low
**Labels:** needs triage

### What happens?

Prior to v1.5.0, `duckdb` would read and execute SQL from standard input. In v1.5.0 it seems that this is no longer the case. I reviewed the release notes and don't see anything indicating that this was a deliberate change, so I'm filing a bug.

### To Reproduce

v1.4.4

```
$ duckdb --version
v1.4.4 (Andium) 6ddac802ff
$ echo "SELECT 1;" | duckdb
┌───────┐
│   1   │
│ int32 │
├───────┤
│   1   │
└───────┘
```

v1.5.0

```
$ duckdb --version
v1.5.0 (Variegata) 3a3967aa81
$ echo "SELECT 1;" | duckdb
$ # no output from above, but $? is 0 indicating success
```

A similar test with `COPY (SELECT 1) TO 'test.csv'` as the query results in a `test.csv` file being created in v1.4.4, but not in v1.5.0, so `duckdb` seems to be ignoring the input entirely (it's not merely an issue of the output being suppressed).

This bug also affects the common pattern of running a SQL script via file input redirection, e.g. `duckdb < analyze.sql`.

### OS:

Debian 13 aarch64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967aa81

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Jake Low

### Affiliation:

OpenStreetMap US

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**marklit:**
I'm seeing the same issue on WSL2 but if I query a Parquet file, it executes without issue.

These all return nothing.

```bash
$ echo "SELECT 1;" | ~/duckdb
$ echo "SELECT 1" | ~/duckdb
$ echo "SELECT 1" | ~/duckdb -json
```

This works as expected:

```bash
$ echo "FROM 'solar_farms.parquet' LIMIT 1" | ~/duckdb -json | jq -S .
```

```json
[
  {
    "bbox": {
      "xmax": -175.21072387695312,
      "xmin": -175.211181640625,
      "ymax": -21.14193344116211,
      "ymin": -21.142297744750977
    },
    "class": "plant",
    "geometry": "POLYGON ((-175.2107254 -21.1422301, -175.2110942 -21.1419337, -175.2111539 -21.1419938, -175.2107812 -21.1422946, -175.2107254 -21.1422301))",
    "height": null,
    "id": "d57d8b8d-bd2c-393e-ab5d-7bc6e8789e1e",
    "level": null,
    "method": "photovoltaic",
    "names": null,
    "operator": null,
    "sources": [
      {
        "between": null,
        "confidence": null,
        "dataset": "OpenStreetMap",
        "property": "",
        "record_id": "w864506948@1",
        "update_time": "2020-10-28T02:27:59.000Z"
      }
    ],
    "subtype": "power",
    "surface": null,
    "version": 0,
    "wikidata": null
  }
]
```

**carlopi:**
This looks like a duplicate of https://github.com/duckdb/duckdb/issues/21243, and the same workaround should apply:

```
DUCKDB_NO_HIGHLIGHT=1 ./build/release/duckdb < test.sql
```
or
```
./build/release/duckdb < test.sql | cat
```

First one skip the relevant codepath when ENV variable is present, second skip relevant codepath via a pipe.
I hope either would work for you as a temporary measure.
