# Internal errors triggered by DELETE after UPDATE and CREATE INDEX

**Issue #21394** | State: closed | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** asd25213
**Labels:** reproduced

### What happens?

Certain sequences of UPDATE followed by CREATE INDEX can leave the index
in an inconsistent state. A subsequent DELETE may trigger internal errors,
including "Failed to delete all rows from index", "UNIQUE constraint
violation", or "Corrupted ART index".

### To Reproduce

### Case 1

```sql
CREATE TABLE t0(c0 INT);
INSERT INTO t0(c0) VALUES (2);
UPDATE t0 SET c0=0;
CREATE INDEX i1 ON t0(c0);
DELETE FROM t0;
```

```
FATAL Error:
Invalid Input Error: Failed to delete all rows from index. Only deleted 0 out of 1 rows.
Chunk: Chunk - [1 Columns]
- FLAT INTEGER: 1 = [ 2]
```

### Case 2

```sql
CREATE TABLE t0(c0 INT, c1 DOUBLE);
INSERT INTO t0(c0, c1) VALUES (1, 1);
UPDATE t0 SET c1=0, c0=0;
CREATE INDEX i1 ON t0(c0);
CREATE INDEX i2 ON t0(c1);
INSERT INTO t0(c0, c1) VALUES (1, 3.1);
DELETE FROM t0;
```

```
terminate called after throwing an instance of 'duckdb::FatalException'
  what():  {"exception_type":"FATAL","exception_message":"FATAL Error: Corrupted ART index - likely the same row id was inserted twice into the same ART"}
```

### Case 3

```sql
CREATE TABLE t0(c0 INT, c1 DOUBLE);
INSERT INTO t0(c0, c1) VALUES (1, 1);
UPDATE t0 SET c1=0, c0=0;
CREATE INDEX i0 ON t0(c1);
CREATE UNIQUE INDEX i1 ON t0(c0);
INSERT INTO t0(c0, c1) VALUES (1, 3.1);
DELETE FROM t0;
```

```
terminate called after throwing an instance of 'duckdb::FatalException'
  what():  {"exception_type":"FATAL","exception_message":"INTERNAL Error: Failed to append to i1: Constraint Error: PRIMARY KEY or UNIQUE constraint violation: duplicate key \"1\"\nThis error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.\nFor more information, see https://duckdb.org/docs/stable/dev/internal_errors\n\nStack Trace:\n\nduckdb() [0xa7c10b]\nduckdb() [0xa7c1c4]\nduckdb() [0xa7f231]\nduckdb() [0xda3867]\nduckdb() [0x509f8f]\nduckdb() [0xf46ee3]\nduckdb() [0xf9646e]\nduckdb() [0xf965ba]\nduckdb() [0xf9721f]\nduckdb() [0x52373e]\nduckdb() [0xf9f88f]\nduckdb() [0xf9b785]\nduckdb() [0xf9bbed]\nduckdb() [0xd66475]\nduckdb() [0xd66a48]\nduckdb() [0xd66fa4]\nduckdb() [0xd679b6]\nduckdb() [0xd67a56]\nduckdb() [0xd6b740]\nduckdb() [0xd6c19d]\nduckdb() [0x85a4e3]\nduckdb() [0x85a7f9]\nduckdb() [0x85aacb]\nduckdb() [0x86566f]\nduckdb() [0x865a66]\nduckdb() [0x836ecf]\n/lib/x86_64-linux-gnu/libc.so.6(+0x2a1ca) [0x7a292ba2a1ca]\n/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x8b) [0x7a292ba2a28b]\nduckdb() [0x83d8be]\n"}
```

### OS:

x86_64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967aa81

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Wang Weipeng

### Affiliation:

Nanjing University of Aeronautics and Astronautics

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@asd25213 thank you! I could reproduce all 3 cases.

**artjomPlaunov:**
thanks for the reproducers @asd25213 we have a PR up here: https://github.com/duckdb/duckdb/pull/21427

**blakethornton651-art:**
Following up on case this is still relevant

On Tue, Mar 17, 2026, 6:45 PM asd25213 ***@***.***> wrote:

> Reopened #21394 .
>
> —
> Reply to this email directly, view it on GitHub
> , or
> unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

**Mytherin:**
All three of these reproducers are instances of the same bug - and they have been fixed in https://github.com/duckdb/duckdb/pull/21427. Thanks again for reporting but I think this one can be closed.
