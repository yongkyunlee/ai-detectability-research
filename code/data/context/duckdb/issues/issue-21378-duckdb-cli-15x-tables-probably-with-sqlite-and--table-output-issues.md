# duckdb cli 1.5.x ".tables" probably with sqlite and "-table" output issues

**Issue #21378** | State: closed | Created: 2026-03-14 | Updated: 2026-03-15
**Author:** ededovic
**Labels:** reproduced

### What happens?

duckdb cli crashes or does not output properly

1. .tables causes internal error - maybe this is sqlite specific
2. duckdb -table repeats fields as many times as there are rows for varchar(>50 or defaults) and timestamp.  Examples below 

### To Reproduce

Several issues: 
1. .tables causes internal error
2. duckdb -tables wraps around

sakila.db can be downloaded `curl -L -O "https://github.com/duckdb/sqlite_scanner/raw/main/data/db/sakila.db"`

`.tables` internal error. It attaches the database and we can see tables with `show tables` but not with `.tables`: 
```duckdb
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D attach 'sakila.db' as s;
memory D show tables ;
┌─────────┐
│  name   │
│ varchar │
└─────────┘
  0 rows
memory D use s;
s D show tables;
┌────────────────────────┐
│          name          │
│        varchar         │
├────────────────────────┤
│ actor                  │
│ address                │
│ category               │
...
│ staff_list             │
│ store                  │
└────────────────────────┘
         21 rows
s D .tables
**INTERNAL Error:**
Unsupported copy type for catalog entry!
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

`-table` cmd line argument repeats some fields like varchar(50) or timestamp. Each field repeats as many rows as shown below:
```
duckdb sakila.db -table   -c 'from customer select email limit 3; '
+-------------------------------------+
|                email                |
+-------------------------------------+
| MARY.SMITH@sakilacustomer.orgPATRICIA.JOHNSON@sakilacustomer.orgLINDA.WILLIAMS@sakilacustomer.org       |
| PATRICIA.JOHNSON@sakilacustomer.orgLINDA.WILLIAMS@sakilacustomer.org |
| LINDA.WILLIAMS@sakilacustomer.org   |
+-------------------------------------+
```
but it works fine on last_name
```duckdb sakila.db -table   -c 'from customer select last_name limit 3; '
+-----------+
| last_name |
+-----------+
| SMITH     |
| JOHNSON   |
| WILLIAMS  |
+-----------+
```
an example with timestamp:

```
duckdb sakila.db  -table -c 'from actor limit 5; '
+----------+------------+--------------+---------------------+
| actor_id | first_name |  last_name   |     last_update     |
+----------+------------+--------------+---------------------+
| 1.0      | PENELOPE   | GUINESS      | 2021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:59 |
| 2.0      | NICK       | WAHLBERG     | 2021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:59 |
| 3.0      | ED         | CHASE        | 2021-03-06 15:51:592021-03-06 15:51:592021-03-06 15:51:59 |
| 4.0      | JENNIFER   | DAVIS        | 2021-03-06 15:51:592021-03-06 15:51:59 |
| 5.0      | JOHNNY     | LOLLOBRIGIDA
                                       | 2021-03-06 15:51:59 |
+----------+------------+--------------+---------------------+
``` 
This is what it should look like:
```
duckdb sakila.db  -c 'from actor limit 5; '
┌──────────┬────────────┬──────────────┬─────────────────────┐
│ actor_id │ first_name │  last_name   │     last_update     │
│  double  │  varchar   │   varchar    │      timestamp      │
├──────────┼────────────┼──────────────┼─────────────────────┤
│      1.0 │ PENELOPE   │ GUINESS      │ 2021-03-06 15:51:59 │
│      2.0 │ NICK       │ WAHLBERG     │ 2021-03-06 15:51:59 │
│      3.0 │ ED         │ CHASE        │ 2021-03-06 15:51:59 │
│      4.0 │ JENNIFER   │ DAVIS        │ 2021-03-06 15:51:59 │
│      5.0 │ JOHNNY     │ LOLLOBRIGIDA │ 2021-03-06 15:51:59 │
└──────────┴────────────┴──────────────┴─────────────────────┘
```

```
duckdb sakila.db  -c 'describe customer '
┌────────────────────────────────────────────┐
│                  customer                  │
│                                            │
│ customer_id bigint    not null             │
│ store_id    bigint    not null             │
│ first_name  varchar   not null             │
│ last_name   varchar   not null             │
│ email       varchar   default NULL         │
│ address_id  bigint    not null             │
│ active      varchar   not null default 'Y' │
│ create_date timestamp not null             │
│ last_update timestamp not null             │
└────────────────────────────────────────────┘
```

### OS:

windows 11 25H2

### DuckDB Version:

1.5.0

### DuckDB Client:

1.5.0

### Hardware:

_No response_

### Full Name:

ed

### Affiliation:

none

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**staticlibs:**
Hi, thanks for the report!

> .tables causes internal error - maybe this is sqlite specific

I believe this is fixed in duckdb/duckdb#21234

> duckdb -table repeats fields as many times as there are rows for varchar(>50 or defaults) and timestamp. Examples below

This is fixed in duckdb/duckdb#21319

Both fixes are intended for 1.5.1 update planned for March 23.

PS: not directly related to the problems above, just to anticipate possible (and usually minor) problems with Unicode - on Windows a custom pager is recommended, see [a warning in docs](https://duckdb.org/docs/current/clients/cli/output_formats).

**carlopi:**
Could you maybe try a nightly binary for `v1.5-variegata` branch? They should have both fixes.

They are available at https://duckdb.org/install/preview (v1.5- + Windows)

**ededovic:**
Thank you. I'm a huge fan of duckdb cli. 

I downloaded the dev version and `-table` is working, but I can not test sqlite because I get the below error. Maybe sqlite and cli are not in sync at the moment. 

```
duckdb
DuckDB v1.5.1-dev183 (Development Version, ba60b17cea)
Enter ".help" for usage hints.
memory D install sqlite;
HTTP Error:
Failed to download extension "sqlite_scanner" at URL "http://extensions.duckdb.org/ba60b17cea/windows_amd64/sqlite_scanner.duckdb_extension.gz" (HTTP 404)
Extension "sqlite_scanner" is an existing extension.

For more info, visit https://duckdb.org/docs/stable/extensions/troubleshooting?version=ba60b17cea&platform=windows_amd64&extension=sqlite_scanner
```

**staticlibs:**
@ededovic 

There is additional fix for this submitted to duckdb-sqlite - duckdb/duckdb-sqlite#178

When it is merged, you can install it with:

```sql
FORCE INSTALL sqlite FROM core_nightly
```

But it will only be compatible with v1.5.0 CLI, so not useful if you need also the updated CLI. All these fixes are going to be synced on 1.5.1.
