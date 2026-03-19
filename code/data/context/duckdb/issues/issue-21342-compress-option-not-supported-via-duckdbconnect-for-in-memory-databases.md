# COMPRESS option not supported via duckdb.connect() for in-memory databases

**Issue #21342** | State: open | Created: 2026-03-12 | Updated: 2026-03-15
**Author:** rustyconover
**Labels:** under review

### What happens?

The `COMPRESS` option introduced in v1.4.0 for in-memory databases can only be enabled via `ATTACH ':memory:' AS db (COMPRESS)`. It cannot be passed through `duckdb.connect(":memory:", config={"compress": "true"})` to enable compression on the default in-memory database at connection time.

This means users must always use the two-step ATTACH + USE pattern rather than simply connecting with compression enabled. It would be more ergonomic and consistent if `compress` were accepted as a connection config option.

### To Reproduce

```python
import duckdb

# This works — compression enabled via ATTACH
con = duckdb.connect(":memory:")
con.execute("ATTACH ':memory:' AS cdb (COMPRESS)")
con.execute("USE cdb")
print(con.execute("SELECT database_name, options FROM duckdb_databases()").fetchall())
# Shows: ('cdb', {'compress': 'true'})
con.close()

# This fails — compress not recognized as a connect() config option
con = duckdb.connect(":memory:", config={"compress": "true"})
# Raises: Invalid Input Error: The following options were not recognized: compress
```

**Expected behavior:** `duckdb.connect(":memory:", config={"compress": "true"})` should open an in-memory database with compression enabled on the default database, equivalent to the ATTACH approach.

### OS:
macOS 15 (Darwin 24.6.0), arm64

### DuckDB Version:
1.5.0

### DuckDB Client:
Python

### Hardware:
Apple Silicon (arm64)

### Full Name:
Rusty Conover

### Affiliation:
Query.Farm

### Related Issues

Related to https://github.com/duckdb/duckdb/issues/19032 which reported a `COMPRESSED` keyword error — this issue is about the broader inconsistency that `compress` is only available as an ATTACH option and not as a connection config parameter.

---

- [x] Did you include all relevant configuration to reproduce the issue?
- [x] Did you include all code required to reproduce the issue?
- Not applicable - the reproduction does not require a data set

## Comments

**MPizzotti:**
@rustyconover i think it's a duplicate of #19032, more than a related error

**Mytherin:**
Thanks for the report - in general `ATTACH` options cannot currently be passed through the initial database configuration. That's a limitation we plan to address eventually.

**rustyconover:**
Thanks @Mytherin!
