# Insert or replace succeeds but doesn't update non-PK indexed columns

**Issue #20952** | State: closed | Created: 2026-02-13 | Updated: 2026-03-17
**Author:** jkeillor
**Labels:** reproduced

### What happens?

Calling `insert or replace` on a table that includes indexes on non-primary key columns executes successfully but doesn't update the other indexed columns.

### To Reproduce

Minimal replication:
```
CREATE TABLE t (id VARCHAR PRIMARY KEY, state VARCHAR NOT NULL, name VARCHAR NOT NULL);
INSERT OR REPLACE INTO t VALUES ('a', 'first', 'jeremy');
CREATE INDEX idx_state ON t(state);
INSERT OR REPLACE INTO t VALUES ('a', 'second','tim');
select * from t;
```
I would expect the select to return "a, second, tim" but get "a,first,tim".

### OS:

Ubuntu 24.04.3 LTS x86_64

### DuckDB Version:

1.4.4

### DuckDB Client:

python, cli

### Hardware:

_No response_

### Full Name:

Jeremy Keillor

### Affiliation:

CIBO Technologies

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**feichai0017:**
I'd like to take a shot at this issue. I'll investigate and open a PR if I can reproduce and fix it.
