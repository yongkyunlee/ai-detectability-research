# Reading JSON from `/dev/stdin` seems broken in `v1.5.0`

**Issue #21469** | State: closed | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** jtbaker
**Labels:** needs triage

### What happens?

There seems to have been a regression with reading json specifically, and possibly other data, from stdin with v1.5.0. Possibly related to #21466 , but notably, this issue does _not_ present in `v1.4.4` while #21466 reportedly does. [The docs](https://duckdb.org/docs/stable/data/json/overview#loading-json)

```sh
 duckdb -version
v1.5.0 (Variegata) 3a3967aa81
➜  ~ echo '[{"name": "Tom"}, {"name": "Jerry"}]' | duckdb -c "FROM read_json('/dev/stdin');"
┌────────┐
│  json  │
│  json  │
└────────┘
  0 rows
```

```sh
duckdb -version
v1.4.4 (Andium) 6ddac802ff
➜  ~ echo '[{"name": "Tom"}, {"name": "Jerry"}]' | duckdb -c "FROM read_json('/dev/stdin');"
┌─────────┐
│  name   │
│ varchar │
├─────────┤
│ Tom     │
│ Jerry   │
└─────────┘
```

```sh
duckdb -version
v1.4.3 (Andium) d1dc88f950
➜  ~ echo '[{"name": "Tom"}, {"name": "Jerry"}]' | duckdb -c "FROM read_json('/dev/stdin');"
┌─────────┐
│  name   │
│ varchar │
├─────────┤
│ Tom     │
│ Jerry   │
└─────────┘
```

### To Reproduce

```sh
echo '[{"name": "Tom"}, {"name": "Jerry"}]' | duckdb -c "FROM read_json('/dev/stdin');"
```

### OS:

MacOS Sequoia v15.7.4

### DuckDB Version:

v1.5.0

### DuckDB Client:

CLI

### Hardware:

Macbook Air M4

### Full Name:

Jason Baker

### Affiliation:

SONAR

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @jtbaker, thanks for opening this issue. This seems to be a duplicate of https://github.com/duckdb/duckdb/issues/21243. The `| cat` trick described there and documented [here](https://duckdb.org/docs/current/guides/troubleshooting/command_line) works around this issue.

We'll ship a proper fix next week in v1.5.1.

**jtbaker:**
> Hi [@jtbaker](https://github.com/jtbaker), thanks for opening this issue. This seems to be a duplicate of [#21243](https://github.com/duckdb/duckdb/issues/21243). The `| cat` trick described there and documented [here](https://duckdb.org/docs/current/guides/troubleshooting/command_line) works around this issue.
> 
> We'll ship a proper fix next week in v1.5.1.

Thanks @szarnyasg! apologies for the duplicate, my issue search-fu didn't turn this up for me. Really appreciate the work you and the team do on this amazing tool!
