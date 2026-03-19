# Out of Range Error when executing prepared statement with unary minus on BIGINT minimum value

**Issue #21077** | State: open | Created: 2026-02-25 | Updated: 2026-03-01
**Author:** Young-Leo
**Labels:** reproduced

### What happens?

### **Description**

There is an inconsistency between how DuckDB handles unary minus operations on the minimum `BIGINT` value (`-9223372036854775808`) in ordinary SQL statements versus prepared statements.

In an **ordinary statement**, DuckDB correctly identifies that negating the minimum `BIGINT` results in a value ($9223372036854775808$) that exceeds the `BIGINT` range and automatically promotes the result to `HUGEINT`.

However, in a **prepared statement**, the negation causes an `Out of Range Error`. It seems the type inference for the placeholder `?` or the return type of the unary minus operator is strictly bound to `BIGINT` during the `PREPARE` phase, failing to account for the necessary type promotion to `HUGEINT` during execution.

### **Expected Behavior**

The prepared statement should behave like the ordinary statement and automatically promote the result to `HUGEINT` without throwing an overflow error.

### **Actual Behavior**

The `EXECUTE` command throws:

> `Out of Range Error: Value "9223372036854775808" is out of range for type BIGINT`

### To Reproduce

### **Reproducible Example**

```sql
-- This works fine (Ordinary statement)
SELECT - -9223372036854775808;

-- This fails (Prepared statement)
PREPARE ps AS SELECT - ?;
EXECUTE ps(-9223372036854775808);

```

### OS:

Windows 11

### DuckDB Version:

v1.4.4

### DuckDB Client:

DuckDB-Wasm (Web Shell)

### Hardware:

_No response_

### Full Name:

Le yang

### Affiliation:

Tsinghua University

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**kchasialis:**
Hello,

I have submitted a PR for this problem
https://github.com/duckdb/duckdb/pull/21130

Please let me know if it works!
