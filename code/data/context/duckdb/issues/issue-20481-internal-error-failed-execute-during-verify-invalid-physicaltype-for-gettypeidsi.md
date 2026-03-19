# INTERNAL Error: Failed execute during verify: Invalid PhysicalType for GetTypeIdSize

**Issue #20481** | State: closed | Created: 2026-01-11 | Updated: 2026-03-13
**Author:** CR7-source
**Labels:** reproduced

### What happens?

INTERNAL Error:
Failed execute during verify: Invalid PhysicalType for GetTypeIdSize

Stack Trace:

duckdb(+0x1587bc1) [0x555b7aa67bc1]
duckdb(+0x15a299b) [0x555b7aa8299b]
duckdb(+0x16e21fd) [0x555b7abc21fd]
duckdb(+0x1177a13) [0x555b7a657a13]
duckdb(+0x1175a8c) [0x555b7a655a8c]
duckdb(+0xf7b3b4) [0x555b7a45b3b4]
duckdb(+0xdda57b) [0x555b7a2ba57b]
duckdb(+0xdd9cc2) [0x555b7a2b9cc2]
duckdb(+0x3072e17) [0x555b7c552e17]
duckdb(+0x305ca98) [0x555b7c53ca98]
duckdb(+0x30133d2) [0x555b7c4f33d2]
duckdb(+0x304c24b) [0x555b7c52c24b]
duckdb(+0x2b8bccd) [0x555b7c06bccd]
duckdb(+0x2b9d83e) [0x555b7c07d83e]
duckdb(+0x2ba2985) [0x555b7c082985]
duckdb(+0x2f6fc40) [0x555b7c44fc40]
duckdb(+0x953e28c) [0x555b82a1e28c]
duckdb(+0x2ba7559) [0x555b7c087559]
duckdb(+0x2b99045) [0x555b7c079045]
duckdb(+0x2ba3b82) [0x555b7c083b82]
duckdb(+0x2bbdba3) [0x555b7c09dba3]
duckdb(+0x2bb2b60) [0x555b7c092b60]
duckdb(+0x2c16469) [0x555b7c0f6469]
duckdb(+0x4dde39) [0x555b799bde39]
duckdb(+0x3f654e) [0x555b798d654e]
duckdb(+0x43898a) [0x555b7991898a]
duckdb(+0x42b2cd) [0x555b7990b2cd]
duckdb(+0x43f820) [0x555b7991f820]
/lib/x86_64-linux-gnu/libc.so.6(+0x29d90) [0x7faeceee4d90]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x80) [0x7faeceee4e40]
duckdb(+0x308e75) [0x555b797e8e75]

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors

### To Reproduce

```
pragma enable_verification;
CREATE TABLE v0 ( v2 INTEGER CHECK( v2 BETWEEN 1 AND 1119 ) , v1 INT ) ; INSERT INTO v0 ( v2 ) VALUES ( 10 ) ; SELECT COALESCE ( LEAD ( 1 ) OVER( ) , ( v1 ) ) > 1 FROM v0 GROUP BY v1
```

### OS:

Ubuntu 22.04.1 LTS x86_64

### DuckDB Version:

DuckDB v1.4.1-dev211 (Development Version) 4f797f8

### DuckDB Client:

duckdb

### Hardware:

_No response_

### Full Name:

smartfuzz

### Affiliation:

smartfuzz

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**taniabogatsch:**
Fix here: https://github.com/duckdb/duckdb/pull/21323
