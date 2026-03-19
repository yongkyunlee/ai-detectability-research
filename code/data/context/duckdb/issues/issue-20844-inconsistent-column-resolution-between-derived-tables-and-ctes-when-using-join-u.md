# Inconsistent Column Resolution Between Derived Tables and CTEs When Using JOIN ... USING Clause

**Issue #20844** | State: closed | Created: 2026-02-06 | Updated: 2026-03-06
**Author:** david-mateo
**Labels:** reproduced, expected behavior

### What happens?

When selecting a non-existent column (`user_id`) from `table_without_user_id` in both a derived table (inline subquery in a JOIN) and a CTE, the SQL engine behaves inconsistently:

- The derived table query (`join (...) h`) does not raise an error and executes successfully, even though `user_id` does not exist in `table_without_user_id`.
- The CTE query (`with h as (...)`) raises an error, as expected, because `user_id` does not exist in `table_without_user_id`.

**Expected Behavior:**

Both queries should behave identically. Attempting to select a column that does not exist in the source table should always result in an error, regardless of whether the selection is made in a derived table or a CTE. The SQL engine should not allow silent column resolution or implicit column creation in one context but not the other.

**Example:**
```SQL
CREATE TABLE table_without_user_id (
	"date" date
);
CREATE TABLE table_with_user_id (
	"date" date,
	user_id int
);
select *
from table_with_user_id
join
    (select "date", user_id from table_without_user_id) as h  -- note that table_without_user_id does not have user_id 
    using ("date", user_id)
;  -- this query works
with h as (select "date", user_id from table_without_user_id)  -- note that table_without_user_id does not have user_id 
select *
from table_with_user_id
join h using ("date", user_id)
;  -- this query fails
```

### To Reproduce

1. Run the following plain SQL query:
```SQL
CREATE TABLE table_without_user_id (
	"date" date
);
CREATE TABLE table_with_user_id (
	"date" date,
	user_id int
);
select *
from table_with_user_id
join
    (select "date", user_id from table_without_user_id) as h  -- note that table_without_user_id does not have user_id 
    using ("date", user_id)
;  -- this query works
```

output:
```
┌──────┬─────────┐
│ date │ user_id │
│ date │  int32  │
├──────┴─────────┤
│     0 rows     │
└────────────────┘
```

2. Run the following plain SQL query:
```SQL
CREATE TABLE table_without_user_id (
	"date" date
);
CREATE TABLE table_with_user_id (
	"date" date,
	user_id int
);
with h as (select "date", user_id from table_without_user_id)  -- note that table_without_user_id does not have user_id 
select *
from table_with_user_id
join h using ("date", user_id)
;  -- this query fails
```

output:
```
Binder Error:
Referenced column "user_id" not found in FROM clause!
Candidate bindings: "date"

LINE 1: with h as (select "date", user_id from table_without_user_id)  -- note that table_wit...
                                  ^
[Command exited with 1]
```

### OS:

macOS 14.6.1 / aarch64

### DuckDB Version:

v1.4.4 (Andium) 6ddac802ff

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

David Mateo

### Affiliation:

Kido Dynamics

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
Paging @kryonix – Denis, could you please take a look at this CTE issue?

**kryonix:**
I will take a look 👍🏻

**kryonix:**
Actually, the CTE does show correct behavior here. The query not using a CTE works, but should not.

**kryonix:**
I took a closer look at this. The behavior may seem unexpected, but it is not a bug.

```
SELECT *
FROM table_with_user_id
JOIN
    (SELECT "date", user_id FROM table_without_user_id) AS h
    USING ("date", user_id)
;
```

The `JOIN` is (implicitly) a `LATERAL` join. As such, `user_id` in subquery `h` is taken from `table_with_user_id`. That's expected behavior.
